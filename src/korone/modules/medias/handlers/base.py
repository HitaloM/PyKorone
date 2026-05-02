from __future__ import annotations

import asyncio
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Any, ClassVar, NotRequired, TypedDict

from aiogram.exceptions import TelegramBadRequest, TelegramNetworkError
from aiogram.types import BufferedInputFile
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.formatting import Bold, Code, Italic, Text, TextLink
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.media_group import MediaGroupBuilder
from stfu_tg import Template

from korone.constants import (
    TELEGRAM_PHOTO_MAX_ASPECT_RATIO,
    TELEGRAM_PHOTO_MAX_DIMENSIONS_SUM,
    TELEGRAM_PHOTO_MAX_FILE_SIZE_BYTES,
)
from korone.filters.chat_status import GroupChatFilter
from korone.logger import get_logger
from korone.modules.medias.filters import MediaUrlFilter
from korone.modules.medias.utils.photo_compression import (
    compress_photo_payload_to_safe_jpeg,
    photo_payload_needs_resize,
)
from korone.modules.medias.utils.types import MediaItem, MediaKind, MediaPost
from korone.modules.medias.utils.url import normalize_media_url
from korone.modules.utils_.file_id_cache import (
    delete_cached_file_payload,
    get_cached_file_payload,
    make_file_id_cache_key,
    set_cached_file_payload,
)
from korone.modules.utils_.telegram_exceptions import REPLIED_NOT_FOUND
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from contextlib import AbstractAsyncContextManager

    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import InlineKeyboardMarkup, Message

    from korone.modules.medias.utils.provider_base import MediaProvider


class MediaCacheEntryPayload(TypedDict, total=False):
    kind: str
    file_id: str
    source_url: str
    duration: int
    width: int
    height: int


class PostCachePayload(TypedDict):
    author_name: str
    author_handle: str
    text: str
    url: str
    website: str
    media: list[MediaCacheEntryPayload]
    quote_text: NotRequired[str]
    quote_author_name: NotRequired[str]
    quote_author_handle: NotRequired[str]


logger = get_logger(__name__)


class BaseMediaHandler(KoroneMessageHandler):
    CAPTION_LIMIT = 1024
    MEDIA_GROUP_LIMIT = 10
    PHOTO_SAFE_LIMIT_BYTES = TELEGRAM_PHOTO_MAX_FILE_SIZE_BYTES - 32 * 1024
    PHOTO_MAX_DIMENSIONS_SUM = TELEGRAM_PHOTO_MAX_DIMENSIONS_SUM
    PHOTO_MAX_ASPECT_RATIO = TELEGRAM_PHOTO_MAX_ASPECT_RATIO
    PHOTO_COMPRESSION_TIMEOUT_SECONDS: ClassVar[float] = 12.0
    MEDIA_SEND_REQUEST_TIMEOUT_SECONDS: ClassVar[int] = 180
    POST_CACHE_NAMESPACE: ClassVar[str] = "media-post"
    MEDIA_SOURCE_CACHE_NAMESPACE: ClassVar[str] = "media-source"
    _MISSING_REPLY_ERROR_TOKENS: ClassVar[tuple[str, ...]] = (REPLIED_NOT_FOUND, "replied message not found")
    _RETRYABLE_PHOTO_ERROR_TOKENS: ClassVar[tuple[str, ...]] = (
        "too big for a photo",
        "photo_invalid_dimensions",
        "invalid dimensions",
        "image_process_failed",
    )
    _REQUEST_TIMEOUT_NETWORK_ERROR_TOKENS: ClassVar[tuple[str, ...]] = ("request timeout error",)

    PROVIDER: ClassVar[type[MediaProvider]]
    DEFAULT_AUTHOR_NAME: ClassVar[str]
    DEFAULT_AUTHOR_HANDLE: ClassVar[str]
    AUTHOR_HANDLE_PREFIX: ClassVar[str] = "@"

    @staticmethod
    def _normalize_telegram_error_message(error: TelegramBadRequest) -> str:
        return error.message.casefold()

    @classmethod
    def _message_contains_any(cls, error: TelegramBadRequest, tokens: tuple[str, ...]) -> bool:
        normalized_message = cls._normalize_telegram_error_message(error)
        return any(token in normalized_message for token in tokens)

    @classmethod
    def _is_missing_reply_error(cls, error: TelegramBadRequest) -> bool:
        return cls._message_contains_any(error, cls._MISSING_REPLY_ERROR_TOKENS)

    @classmethod
    def _is_retryable_photo_send_error(cls, error: TelegramBadRequest) -> bool:
        return cls._message_contains_any(error, cls._RETRYABLE_PHOTO_ERROR_TOKENS)

    @classmethod
    def _is_request_timeout_network_error(cls, error: TelegramNetworkError) -> bool:
        normalized_message = str(error).casefold()
        return any(token in normalized_message for token in cls._REQUEST_TIMEOUT_NETWORK_ERROR_TOKENS)

    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:  # pyright: ignore[reportIncompatibleMethodOverride]
        return (GroupChatFilter(), MediaUrlFilter(cls.PROVIDER.pattern))

    @staticmethod
    def _post_cache_candidates(url: str) -> list[str]:
        if not (normalized_url := url.strip()):
            return []

        return [normalized_url]

    @classmethod
    def _collect_post_cache_candidates(cls, *urls: str) -> set[str]:
        return {candidate for url in urls for candidate in cls._post_cache_candidates(url)}

    @classmethod
    def _post_cache_key(cls, url: str) -> str:
        return make_file_id_cache_key(cls.POST_CACHE_NAMESPACE, url)

    @classmethod
    def _media_source_cache_key(cls, source_url: str) -> str:
        cache_identifier = normalize_media_url(source_url) or source_url.strip() or source_url
        return make_file_id_cache_key(cls.MEDIA_SOURCE_CACHE_NAMESPACE, cache_identifier)

    @staticmethod
    def _extract_sent_file_id(sent_message: Message, kind: MediaKind) -> str | None:
        match kind:
            case MediaKind.PHOTO if sent_message.photo:
                return sent_message.photo[-1].file_id
            case MediaKind.VIDEO if sent_message.video:
                return sent_message.video.file_id
            case _:
                return None

    @staticmethod
    def _coerce_cached_int(value: object) -> int | None:
        return value if isinstance(value, int) and not isinstance(value, bool) else None

    @staticmethod
    def _serialize_media_cache_entry(media: MediaItem, file_id: str) -> MediaCacheEntryPayload:
        payload: MediaCacheEntryPayload = {"kind": media.kind.value, "file_id": file_id, "source_url": media.source_url}

        if media.duration is not None:
            payload["duration"] = media.duration
        if media.width is not None:
            payload["width"] = media.width
        if media.height is not None:
            payload["height"] = media.height

        return payload

    @classmethod
    def _deserialize_media_cache_entry(cls, payload: dict[str, Any], index: int) -> MediaItem | None:
        match payload:
            case {"kind": str() as kind_raw, "file_id": str() as file_id, **rest} if file_id:
                try:
                    kind = MediaKind(kind_raw)
                except ValueError:
                    return None
            case _:
                return None

        source_url = rest.get("source_url")
        if not isinstance(source_url, str) or not source_url:
            source_url = f"cached://{index}"

        return MediaItem(
            kind=kind,
            file=file_id,
            filename=f"cached_media_{index}",
            source_url=source_url,
            duration=cls._coerce_cached_int(rest.get("duration")),
            width=cls._coerce_cached_int(rest.get("width")),
            height=cls._coerce_cached_int(rest.get("height")),
        )

    @classmethod
    def _build_post_cache_payload(
        cls, post: MediaPost, media_payload: list[MediaCacheEntryPayload]
    ) -> PostCachePayload:
        payload: PostCachePayload = {
            "author_name": post.author_name,
            "author_handle": post.author_handle,
            "text": post.text,
            "url": post.url,
            "website": post.website,
            "media": media_payload,
        }

        if post.quote_text:
            payload["quote_text"] = post.quote_text
        if post.quote_author_name:
            payload["quote_author_name"] = post.quote_author_name
        if post.quote_author_handle:
            payload["quote_author_handle"] = post.quote_author_handle

        return payload

    @classmethod
    def _deserialize_post_cache_payload(cls, payload: dict[str, Any]) -> MediaPost | None:
        match payload:
            case {"media": list(raw_media), "url": str() as url, "website": str() as website, **rest} if (
                url and website
            ):
                pass
            case _:
                return None

        media_items: list[MediaItem] = []
        for index, entry in enumerate(raw_media, start=1):
            if not isinstance(entry, dict):
                return None
            media_item = cls._deserialize_media_cache_entry(entry, index)
            if media_item is None:
                return None
            media_items.append(media_item)

        if not media_items:
            return None

        author_name = rest.get("author_name")
        author_handle = rest.get("author_handle")
        text = rest.get("text")
        quote_text = rest.get("quote_text")
        quote_author_name = rest.get("quote_author_name")
        quote_author_handle = rest.get("quote_author_handle")

        return MediaPost(
            author_name=author_name if isinstance(author_name, str) and author_name else cls.DEFAULT_AUTHOR_NAME,
            author_handle=author_handle if isinstance(author_handle, str) else cls.DEFAULT_AUTHOR_HANDLE,
            text=text if isinstance(text, str) else "",
            url=url,
            website=website,
            media=media_items,
            quote_text=quote_text if isinstance(quote_text, str) and quote_text else None,
            quote_author_name=quote_author_name if isinstance(quote_author_name, str) and quote_author_name else None,
            quote_author_handle=(
                quote_author_handle if isinstance(quote_author_handle, str) and quote_author_handle else None
            ),
        )

    async def _get_cached_post(self, source_url: str) -> tuple[str, MediaPost] | None:
        for candidate_url in self._post_cache_candidates(source_url):
            cache_key = self._post_cache_key(candidate_url)
            cached_payload = await get_cached_file_payload(cache_key)
            if not cached_payload:
                continue

            cached_post = self._deserialize_post_cache_payload(cached_payload)
            if cached_post:
                return candidate_url, cached_post

            await delete_cached_file_payload(cache_key)

        return None

    async def _delete_post_cache(self, *urls: str) -> None:
        for candidate_url in self._collect_post_cache_candidates(*urls):
            await delete_cached_file_payload(self._post_cache_key(candidate_url))

    async def _set_post_cache(
        self, source_url: str, post: MediaPost, media_payload: list[MediaCacheEntryPayload]
    ) -> None:
        if not media_payload:
            return

        payload = self._build_post_cache_payload(post, media_payload)
        for candidate_url in self._collect_post_cache_candidates(source_url, post.url):
            await set_cached_file_payload(self._post_cache_key(candidate_url), payload)

    def _chat_action_kwargs(self) -> dict[str, Any]:
        return {"chat_id": self.event.chat.id, "bot": self.bot, "message_thread_id": self.event.message_thread_id}

    def _upload_action(self, kind: MediaKind) -> AbstractAsyncContextManager[Any]:
        kwargs = self._chat_action_kwargs()
        match kind:
            case MediaKind.PHOTO:
                return ChatActionSender.upload_photo(**kwargs)
            case MediaKind.VIDEO:
                return ChatActionSender.upload_video(**kwargs)
            case _:
                msg = f"Unsupported media kind: {kind!r}"
                raise ValueError(msg)

    @classmethod
    def _compressed_photo_filename(cls, original_name: str) -> str:
        stem = Path(original_name).stem or "photo"
        return f"{stem}_compressed.jpg"

    @classmethod
    def _needs_photo_compression(cls, media: MediaItem) -> bool:
        if media.kind != MediaKind.PHOTO or not isinstance(media.file, BufferedInputFile):
            return False

        if len(media.file.data) > cls.PHOTO_SAFE_LIMIT_BYTES:
            return True

        return photo_payload_needs_resize(
            media.file.data,
            max_dimensions_sum=cls.PHOTO_MAX_DIMENSIONS_SUM,
            max_aspect_ratio=cls.PHOTO_MAX_ASPECT_RATIO,
        )

    async def _compress_photo(self, media: MediaItem, *, force: bool = False) -> MediaItem:
        if media.kind != MediaKind.PHOTO or not isinstance(media.file, BufferedInputFile):
            return media
        if not force and not self._needs_photo_compression(media):
            return media

        try:
            async with asyncio.timeout(self.PHOTO_COMPRESSION_TIMEOUT_SECONDS):
                compressed_payload = await asyncio.to_thread(
                    compress_photo_payload_to_safe_jpeg,
                    media.file.data,
                    safe_limit_bytes=self.PHOTO_SAFE_LIMIT_BYTES,
                    max_dimensions_sum=self.PHOTO_MAX_DIMENSIONS_SUM,
                    max_aspect_ratio=self.PHOTO_MAX_ASPECT_RATIO,
                )
        except TimeoutError:
            await logger.adebug(
                "[Medias] Photo compression timed out",
                source_url=media.source_url,
                timeout_seconds=self.PHOTO_COMPRESSION_TIMEOUT_SECONDS,
            )
            return media
        except Exception:  # noqa: BLE001
            return media

        if not compressed_payload:
            return media

        filename = self._compressed_photo_filename(media.filename)
        return replace(media, file=BufferedInputFile(compressed_payload, filename), filename=filename)

    async def _prepare_photos_for_send(self, media_items: list[MediaItem], *, force: bool) -> list[MediaItem]:
        indexes_to_process = [
            index
            for index, item in enumerate(media_items)
            if item.kind == MediaKind.PHOTO and (force or self._needs_photo_compression(item))
        ]
        if not indexes_to_process:
            return media_items

        prepared = media_items.copy()
        tasks: dict[int, asyncio.Task[MediaItem]] = {}
        async with asyncio.TaskGroup() as tg:
            for index in indexes_to_process:
                tasks[index] = tg.create_task(self._compress_photo(media_items[index], force=force))

        for index, task in tasks.items():
            prepared[index] = task.result()
        return prepared

    async def _prepare_media_items_for_send(self, media_items: list[MediaItem]) -> list[MediaItem]:
        return await self._prepare_photos_for_send(media_items, force=False)

    async def _force_prepare_photos_for_send(self, media_items: list[MediaItem]) -> list[MediaItem]:
        return await self._prepare_photos_for_send(media_items, force=True)

    async def _reply_or_send_photo(
        self, media: MediaItem, caption: str, keyboard: InlineKeyboardMarkup | None, *, reply: bool
    ) -> Message:
        if reply:
            return await self.event.reply_photo(
                media.file,
                caption=caption,
                reply_markup=keyboard,
                request_timeout=self.MEDIA_SEND_REQUEST_TIMEOUT_SECONDS,
            )

        return await self.bot.send_photo(
            chat_id=self.event.chat.id,
            photo=media.file,
            caption=caption,
            reply_markup=keyboard,
            message_thread_id=self.event.message_thread_id,
            request_timeout=self.MEDIA_SEND_REQUEST_TIMEOUT_SECONDS,
        )

    async def _send_photo_with_resize_fallback(
        self, media: MediaItem, caption: str, keyboard: InlineKeyboardMarkup | None, *, reply: bool
    ) -> Message:
        try:
            return await self._reply_or_send_photo(media, caption, keyboard, reply=reply)
        except TelegramBadRequest as error:
            if not self._is_retryable_photo_send_error(error):
                raise
            oversized_error = error

        compressed = await self._compress_photo(media, force=True)
        if compressed is media:
            raise oversized_error

        return await self._reply_or_send_photo(compressed, caption, keyboard, reply=reply)

    async def _reply_or_send_video(
        self, media: MediaItem, caption: str, keyboard: InlineKeyboardMarkup | None, *, reply: bool
    ) -> Message:
        if reply:
            return await self.event.reply_video(
                media.file,
                caption=caption,
                reply_markup=keyboard,
                duration=media.duration,
                width=media.width,
                height=media.height,
                thumbnail=media.thumbnail,
                request_timeout=self.MEDIA_SEND_REQUEST_TIMEOUT_SECONDS,
            )

        return await self.bot.send_video(
            chat_id=self.event.chat.id,
            video=media.file,
            caption=caption,
            reply_markup=keyboard,
            duration=media.duration,
            width=media.width,
            height=media.height,
            thumbnail=media.thumbnail,
            message_thread_id=self.event.message_thread_id,
            request_timeout=self.MEDIA_SEND_REQUEST_TIMEOUT_SECONDS,
        )

    async def _dispatch_media_send(
        self, media: MediaItem, caption: str, keyboard: InlineKeyboardMarkup | None, *, reply: bool
    ) -> Message:
        match media.kind:
            case MediaKind.PHOTO:
                return await self._send_photo_with_resize_fallback(media, caption, keyboard, reply=reply)
            case MediaKind.VIDEO:
                return await self._reply_or_send_video(media, caption, keyboard, reply=reply)
            case _:
                msg = f"Unsupported media kind: {media.kind!r}"
                raise ValueError(msg)

    async def _reply_media(self, media: MediaItem, caption: str, keyboard: InlineKeyboardMarkup | None) -> Message:
        return await self._dispatch_media_send(media, caption, keyboard, reply=True)

    async def _send_media(self, media: MediaItem, caption: str, keyboard: InlineKeyboardMarkup | None) -> Message:
        return await self._dispatch_media_send(media, caption, keyboard, reply=False)

    @classmethod
    async def _cache_media_source_file_id(cls, source_url: str, file_id: str) -> None:
        await set_cached_file_payload(cls._media_source_cache_key(source_url), {"file_id": file_id})

    async def _cache_sent_media(self, media: MediaItem, sent_message: Message) -> MediaCacheEntryPayload | None:
        if not (file_id := self._extract_sent_file_id(sent_message, media.kind)):
            return None

        await self._cache_media_source_file_id(media.source_url, file_id)
        return self._serialize_media_cache_entry(media, file_id)

    async def _send_single_media(
        self, media: MediaItem, caption: str, keyboard: InlineKeyboardMarkup | None
    ) -> list[MediaCacheEntryPayload]:
        media = await self._compress_photo(media, force=False)
        async with self._upload_action(media.kind):
            try:
                sent_message = await self._reply_media(media, caption, keyboard)
            except TelegramBadRequest as error:
                if not self._is_missing_reply_error(error):
                    raise
                sent_message = await self._send_media(media, caption, keyboard)

        if not (serialized := await self._cache_sent_media(media, sent_message)):
            return []

        return [serialized]

    @staticmethod
    def _add_group_item(builder: MediaGroupBuilder, item: MediaItem, caption: str | None) -> None:
        match item.kind:
            case MediaKind.PHOTO:
                builder.add_photo(item.file, caption=caption)
            case MediaKind.VIDEO:
                builder.add_video(
                    item.file,
                    caption=caption,
                    duration=item.duration,
                    width=item.width,
                    height=item.height,
                    thumbnail=item.thumbnail,
                )
            case _:
                msg = f"Unsupported media kind: {item.kind!r}"
                raise ValueError(msg)

    async def _send_media_group_messages(self, media_group: list[Any]) -> list[Message]:
        try:
            return await self.bot.send_media_group(
                chat_id=self.event.chat.id,
                media=media_group,
                reply_to_message_id=self.event.message_id,
                message_thread_id=self.event.message_thread_id,
                request_timeout=self.MEDIA_SEND_REQUEST_TIMEOUT_SECONDS,
            )
        except TelegramBadRequest as error:
            if not self._is_missing_reply_error(error):
                raise
            return await self.bot.send_media_group(
                chat_id=self.event.chat.id,
                media=media_group,
                message_thread_id=self.event.message_thread_id,
                request_timeout=self.MEDIA_SEND_REQUEST_TIMEOUT_SECONDS,
            )

    def _build_media_group(self, media_items: list[MediaItem], caption: str) -> list[Any]:
        builder = MediaGroupBuilder()
        last_index = len(media_items) - 1
        for index, item in enumerate(media_items):
            self._add_group_item(builder, item, caption if index == last_index else None)

        return builder.build()

    async def _send_media_group(self, media_items: list[MediaItem], caption: str) -> list[MediaCacheEntryPayload]:
        try:
            media_group = self._build_media_group(media_items, caption)
            sent_messages = await self._send_media_group_messages(media_group)
        except TelegramBadRequest as error:
            if not self._is_retryable_photo_send_error(error):
                raise

            forced_media_items = await self._force_prepare_photos_for_send(media_items)
            if forced_media_items == media_items:
                raise

            media_group = self._build_media_group(forced_media_items, caption)
            sent_messages = await self._send_media_group_messages(media_group)
            media_items = forced_media_items

        cached_media_payload: list[MediaCacheEntryPayload] = []
        for item, sent in zip(media_items, sent_messages, strict=False):
            if serialized := await self._cache_sent_media(item, sent):
                cached_media_payload.append(serialized)

        return cached_media_payload

    @classmethod
    def _caption_title(cls, author_name: str, author_handle: str) -> Text:
        normalized_handle = author_handle.lstrip("@")
        handle = f"{cls.AUTHOR_HANDLE_PREFIX}{normalized_handle}" if normalized_handle else normalized_handle
        return Text(Bold(author_name), " (", Code(handle), "):")

    @staticmethod
    def _open_in_website_text(website: str) -> str:
        return str(Template(_("Open in {website}"), website=website))

    @classmethod
    def _caption_link(cls, post: MediaPost, *, include_link: bool) -> Text | None:
        if not include_link:
            return None

        return TextLink(cls._open_in_website_text(post.website), url=post.url)

    @classmethod
    def _render_caption(cls, title: Text, link: Text | None, text: str | None = None) -> str:
        blocks: list[Text] = [title]
        if text:
            blocks.append(Italic(text))
        if link:
            blocks.append(link)

        rendered_blocks: list[Text | str] = []
        for block in blocks:
            if rendered_blocks:
                rendered_blocks.append("\n\n")
            rendered_blocks.append(block)

        return Text(*rendered_blocks, sep="").as_html()

    @classmethod
    def _build_caption(cls, post: MediaPost, *, include_link: bool) -> str:
        title = cls._caption_title(
            post.author_name or cls.DEFAULT_AUTHOR_NAME, post.author_handle or cls.DEFAULT_AUTHOR_HANDLE
        )
        link = cls._caption_link(post, include_link=include_link)

        if not post.text:
            return cls._render_caption(title, link)

        raw_text = post.text
        candidate = cls._render_caption(title, link, raw_text)
        if len(candidate) <= cls.CAPTION_LIMIT:
            return candidate

        trimmed_text = cls._truncate_text(raw_text, title, link)
        if not trimmed_text:
            return cls._render_caption(title, link)

        return cls._render_caption(title, link, trimmed_text)

    @classmethod
    def _truncate_text(cls, raw_text: str, title: Text, link: Text | None) -> str:
        ellipsis = " [...]"
        low = 0
        high = len(raw_text)
        best = ""

        while low <= high:
            mid = (low + high) // 2
            truncated = raw_text[:mid].rstrip()
            text = f"{truncated}{ellipsis}" if truncated else ""
            candidate = cls._render_caption(title, link, text or None)

            if len(candidate) <= cls.CAPTION_LIMIT:
                best = text
                low = mid + 1
            else:
                high = mid - 1

        return best

    @staticmethod
    def _build_keyboard(post: MediaPost) -> InlineKeyboardMarkup | None:
        builder = InlineKeyboardBuilder()
        builder.button(text=BaseMediaHandler._open_in_website_text(post.website), url=post.url)
        return builder.as_markup()

    async def _fetch_post(self, url: str) -> MediaPost | None:
        async with ChatActionSender.typing(**self._chat_action_kwargs()):
            return await self.PROVIDER.safe_fetch(url)

    async def _send_post(self, post: MediaPost) -> list[MediaCacheEntryPayload]:
        media_items = post.media[: self.MEDIA_GROUP_LIMIT]
        if not media_items:
            return []

        media_items = await self._prepare_media_items_for_send(media_items)
        caption = self._build_caption(post, include_link=False)
        keyboard = self._build_keyboard(post)

        if len(media_items) == 1:
            cached_media_payload = await self._send_single_media(media_items[0], caption, keyboard)
            if len(cached_media_payload) != 1:
                return []
            return cached_media_payload

        group_caption = self._build_caption(post, include_link=True)
        async with ChatActionSender.upload_document(**self._chat_action_kwargs()):
            cached_media_payload = await self._send_media_group(media_items, group_caption)

        if len(cached_media_payload) != len(media_items):
            return []
        return cached_media_payload

    async def _try_send_cached_post(self, source_url: str) -> bool:
        if not (cached_post_payload := await self._get_cached_post(source_url)):
            return False

        cached_url, cached_post = cached_post_payload
        try:
            cached_media_payload = await self._send_post(cached_post)
        except TelegramBadRequest:
            await self._delete_post_cache(source_url, cached_url, cached_post.url)
            return False

        if cached_media_payload:
            await self._set_post_cache(source_url, cached_post, cached_media_payload)
        return True

    async def handle(self) -> None:
        if not self.bot:
            return

        source_url: str | None = None
        try:
            match self.data.get("media_urls"):
                case [str() as source_url, *_]:
                    pass
                case _:
                    return

            if await self._try_send_cached_post(source_url):
                await logger.adebug("[Medias] Cached post sent", provider=self.PROVIDER.name, source_url=source_url)
                return

            post = await self._fetch_post(source_url)
            if not post:
                await logger.adebug("[Medias] Could not fetch post", provider=self.PROVIDER.name, source_url=source_url)
                return

            cached_media_payload = await self._send_post(post)
            if not cached_media_payload:
                await logger.adebug(
                    "[Medias] Could not send media",
                    provider=self.PROVIDER.name,
                    source_url=source_url,
                    post_url=post.url,
                    media_count=len(post.media),
                )
                return

            await self._set_post_cache(source_url, post, cached_media_payload)
        except asyncio.CancelledError:
            raise
        except TelegramNetworkError as error:
            if self._is_request_timeout_network_error(error):
                await logger.awarning(
                    "[Medias] Media send request timed out; delivery status is unknown",
                    provider=self.PROVIDER.name,
                    source_url=source_url,
                    chat_id=self.event.chat.id,
                    message_id=self.event.message_id,
                    message_thread_id=self.event.message_thread_id,
                    handler=self.__class__.__name__,
                    request_timeout_seconds=self.MEDIA_SEND_REQUEST_TIMEOUT_SECONDS,
                )
                return

            await logger.aexception(
                "[Medias] Handler failed",
                provider=self.PROVIDER.name,
                source_url=source_url,
                chat_id=self.event.chat.id,
                message_id=self.event.message_id,
                message_thread_id=self.event.message_thread_id,
                handler=self.__class__.__name__,
            )
        except Exception:  # noqa: BLE001
            await logger.aexception(
                "[Medias] Handler failed",
                provider=self.PROVIDER.name,
                source_url=source_url,
                chat_id=self.event.chat.id,
                message_id=self.event.message_id,
                message_thread_id=self.event.message_thread_id,
                handler=self.__class__.__name__,
            )

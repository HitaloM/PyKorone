from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar
from urllib.parse import urldefrag

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardButton
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.media_group import MediaGroupBuilder
from stfu_tg import Bold, Code, Italic, Template, Url

from korone.filters.chat_status import GroupChatFilter
from korone.modules.medias.filters import MediaUrlFilter
from korone.modules.medias.utils.base import MediaItem, MediaKind, MediaPost
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
    from stfu_tg.doc import Element

    from korone.modules.medias.utils.base import MediaProvider

type CachePayload = dict[str, Any]


class BaseMediaHandler(KoroneMessageHandler):
    CAPTION_LIMIT = 1024
    MEDIA_GROUP_LIMIT = 10
    POST_CACHE_NAMESPACE: ClassVar[str] = "media-post"
    MEDIA_SOURCE_CACHE_NAMESPACE: ClassVar[str] = "media-source"

    PROVIDER: ClassVar[type[MediaProvider]]
    DEFAULT_AUTHOR_NAME: ClassVar[str]
    DEFAULT_AUTHOR_HANDLE: ClassVar[str]

    @staticmethod
    def _is_missing_reply_error(error: TelegramBadRequest) -> bool:
        normalized_message = error.message.lower()
        return REPLIED_NOT_FOUND in normalized_message or "replied message not found" in normalized_message

    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:  # pyright: ignore[reportIncompatibleMethodOverride]
        return (GroupChatFilter(), MediaUrlFilter(cls.PROVIDER.pattern))

    @staticmethod
    def _post_cache_candidates(url: str) -> list[str]:
        if not (normalized_url := url.strip()):
            return []

        without_fragment, _ = urldefrag(normalized_url)
        return list(
            dict.fromkeys(
                candidate for candidate in (normalized_url, without_fragment, without_fragment.rstrip("/")) if candidate
            )
        )

    @classmethod
    def _collect_post_cache_candidates(cls, *urls: str) -> set[str]:
        return {candidate for url in urls for candidate in cls._post_cache_candidates(url)}

    @classmethod
    def _post_cache_key(cls, url: str) -> str:
        return make_file_id_cache_key(cls.POST_CACHE_NAMESPACE, url)

    @classmethod
    def _media_source_cache_key(cls, source_url: str) -> str:
        return make_file_id_cache_key(cls.MEDIA_SOURCE_CACHE_NAMESPACE, source_url)

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
    def _serialize_media_cache_entry(media: MediaItem, file_id: str) -> CachePayload:
        payload: CachePayload = {"kind": media.kind.value, "file_id": file_id, "source_url": media.source_url}

        if media.duration is not None:
            payload["duration"] = media.duration
        if media.width is not None:
            payload["width"] = media.width
        if media.height is not None:
            payload["height"] = media.height

        return payload

    @classmethod
    def _deserialize_media_cache_entry(cls, payload: CachePayload, index: int) -> MediaItem | None:
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
    def _build_post_cache_payload(cls, post: MediaPost, media_payload: list[CachePayload]) -> CachePayload:
        return {
            "author_name": post.author_name,
            "author_handle": post.author_handle,
            "text": post.text,
            "url": post.url,
            "website": post.website,
            "media": media_payload,
        }

    @classmethod
    def _deserialize_post_cache_payload(cls, payload: CachePayload) -> MediaPost | None:
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

        return MediaPost(
            author_name=author_name if isinstance(author_name, str) and author_name else cls.DEFAULT_AUTHOR_NAME,
            author_handle=author_handle if isinstance(author_handle, str) else cls.DEFAULT_AUTHOR_HANDLE,
            text=text if isinstance(text, str) else "",
            url=url,
            website=website,
            media=media_items,
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

    async def _set_post_cache(self, source_url: str, post: MediaPost, media_payload: list[CachePayload]) -> None:
        if not media_payload:
            return

        payload = self._build_post_cache_payload(post, media_payload)
        for candidate_url in self._collect_post_cache_candidates(source_url, post.url):
            await set_cached_file_payload(self._post_cache_key(candidate_url), payload)

    def _chat_action_kwargs(self) -> CachePayload:
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

    async def _reply_media(self, media: MediaItem, caption: str, keyboard: InlineKeyboardMarkup | None) -> Message:
        match media.kind:
            case MediaKind.PHOTO:
                return await self.event.reply_photo(media.file, caption=caption, reply_markup=keyboard)
            case MediaKind.VIDEO:
                return await self.event.reply_video(
                    media.file,
                    caption=caption,
                    reply_markup=keyboard,
                    duration=media.duration,
                    width=media.width,
                    height=media.height,
                    thumbnail=media.thumbnail,
                )
            case _:
                msg = f"Unsupported media kind: {media.kind!r}"
                raise ValueError(msg)

    async def _send_media(self, media: MediaItem, caption: str, keyboard: InlineKeyboardMarkup | None) -> Message:
        match media.kind:
            case MediaKind.PHOTO:
                return await self.bot.send_photo(
                    chat_id=self.event.chat.id,
                    photo=media.file,
                    caption=caption,
                    reply_markup=keyboard,
                    message_thread_id=self.event.message_thread_id,
                )
            case MediaKind.VIDEO:
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
                )
            case _:
                msg = f"Unsupported media kind: {media.kind!r}"
                raise ValueError(msg)

    @classmethod
    async def _cache_media_source_file_id(cls, source_url: str, file_id: str) -> None:
        await set_cached_file_payload(cls._media_source_cache_key(source_url), {"file_id": file_id})

    async def _cache_sent_media(self, media: MediaItem, sent_message: Message) -> CachePayload | None:
        if not (file_id := self._extract_sent_file_id(sent_message, media.kind)):
            return None

        await self._cache_media_source_file_id(media.source_url, file_id)
        return self._serialize_media_cache_entry(media, file_id)

    async def _send_single_media(
        self, media: MediaItem, caption: str, keyboard: InlineKeyboardMarkup | None
    ) -> list[CachePayload]:
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
            )
        except TelegramBadRequest as error:
            if not self._is_missing_reply_error(error):
                raise
            return await self.bot.send_media_group(
                chat_id=self.event.chat.id, media=media_group, message_thread_id=self.event.message_thread_id
            )

    async def _send_media_group(self, media_items: list[MediaItem], caption: str) -> list[CachePayload]:
        builder = MediaGroupBuilder()
        last_index = len(media_items) - 1
        for index, item in enumerate(media_items):
            self._add_group_item(builder, item, caption if index == last_index else None)

        media_group = builder.build()
        sent_messages = await self._send_media_group_messages(media_group)

        cached_media_payload: list[CachePayload] = []
        for item, sent in zip(media_items, sent_messages, strict=False):
            if serialized := await self._cache_sent_media(item, sent):
                cached_media_payload.append(serialized)

        return cached_media_payload

    @classmethod
    def _caption_title(cls, author_name: str, author_handle: str) -> Element:
        return Template("{author} ({handle})", author=Bold(author_name), handle=Code(author_handle))

    @classmethod
    def _caption_link(cls, post: MediaPost, *, include_link: bool) -> Element | None:
        if not include_link:
            return None

        return Url(Template(_("Open in {website}"), website=post.website), post.url)

    @classmethod
    def _render_caption(cls, title: Element, link: Element | None, text: str | None = None) -> str:
        link_block: Element | str = Template("\n\n{link}", link=link) if link else ""
        if not text:
            return Template("{title}{link}", title=title, link=link_block).to_html()

        return Template("{title}\n\n{text}{link}", title=title, text=Italic(text), link=link_block).to_html()

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
    def _truncate_text(cls, raw_text: str, title: Element, link: Element | None) -> str:
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
        builder.add(
            InlineKeyboardButton(text=Template(_("Open in {website}"), website=post.website).to_html(), url=post.url)
        )
        return builder.as_markup()

    async def _fetch_post(self, url: str) -> MediaPost | None:
        async with ChatActionSender.typing(**self._chat_action_kwargs()):
            return await self.PROVIDER.fetch(url)

    async def _send_post(self, post: MediaPost) -> list[CachePayload]:
        media_items = post.media[: self.MEDIA_GROUP_LIMIT]
        if not media_items:
            return []

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

        match self.data.get("media_urls"):
            case [str() as source_url, *_]:
                pass
            case _:
                return

        if await self._try_send_cached_post(source_url):
            return

        post = await self._fetch_post(source_url)
        if not post:
            return

        cached_media_payload = await self._send_post(post)
        if not cached_media_payload:
            return

        await self._set_post_cache(source_url, post, cached_media_payload)

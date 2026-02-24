from __future__ import annotations

from typing import TYPE_CHECKING, Any, ClassVar, cast
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
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import InlineKeyboardMarkup, Message
    from stfu_tg.doc import Element

    from korone.modules.medias.utils.base import MediaProvider


class BaseMediaHandler(KoroneMessageHandler):
    CAPTION_LIMIT = 1024
    MEDIA_GROUP_LIMIT = 10
    POST_CACHE_NAMESPACE: ClassVar[str] = "media-post"

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
        normalized_url = url.strip()
        if not normalized_url:
            return []

        without_fragment, _ = urldefrag(normalized_url)
        without_trailing_slash = without_fragment.rstrip("/")

        candidates: list[str] = []
        for candidate in (normalized_url, without_fragment, without_trailing_slash):
            if candidate and candidate not in candidates:
                candidates.append(candidate)

        return candidates

    @classmethod
    def _post_cache_key(cls, url: str) -> str:
        return make_file_id_cache_key(cls.POST_CACHE_NAMESPACE, url)

    @staticmethod
    def _extract_sent_file_id(sent_message: Message, kind: MediaKind) -> str | None:
        if kind == MediaKind.PHOTO and sent_message.photo:
            return sent_message.photo[-1].file_id
        if kind == MediaKind.VIDEO and sent_message.video:
            return sent_message.video.file_id
        return None

    @staticmethod
    def _coerce_cached_int(value: object) -> int | None:
        return value if isinstance(value, int) and not isinstance(value, bool) else None

    @staticmethod
    def _serialize_media_cache_entry(media: MediaItem, file_id: str) -> dict[str, Any]:
        payload: dict[str, Any] = {"kind": media.kind.value, "file_id": file_id, "source_url": media.source_url}

        if media.duration is not None:
            payload["duration"] = media.duration
        if media.width is not None:
            payload["width"] = media.width
        if media.height is not None:
            payload["height"] = media.height

        return payload

    @classmethod
    def _deserialize_media_cache_entry(cls, payload: dict[str, Any], index: int) -> MediaItem | None:
        kind_raw = payload.get("kind")
        file_id = payload.get("file_id")
        source_url = payload.get("source_url")
        if not isinstance(kind_raw, str) or kind_raw not in {MediaKind.PHOTO.value, MediaKind.VIDEO.value}:
            return None
        if not isinstance(file_id, str) or not file_id:
            return None

        if not isinstance(source_url, str) or not source_url:
            source_url = f"cached://{index}"

        return MediaItem(
            kind=MediaKind(kind_raw),
            file=file_id,
            filename=f"cached_media_{index}",
            source_url=source_url,
            duration=cls._coerce_cached_int(payload.get("duration")),
            width=cls._coerce_cached_int(payload.get("width")),
            height=cls._coerce_cached_int(payload.get("height")),
        )

    @classmethod
    def _build_post_cache_payload(cls, post: MediaPost, media_payload: list[dict[str, Any]]) -> dict[str, Any]:
        return {
            "author_name": post.author_name,
            "author_handle": post.author_handle,
            "text": post.text,
            "url": post.url,
            "website": post.website,
            "media": media_payload,
        }

    @classmethod
    def _deserialize_post_cache_payload(cls, payload: dict[str, Any]) -> MediaPost | None:
        raw_media = payload.get("media")
        if not isinstance(raw_media, list):
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

        author_name = payload.get("author_name")
        author_handle = payload.get("author_handle")
        text = payload.get("text")
        url = payload.get("url")
        website = payload.get("website")

        if not isinstance(url, str) or not url:
            return None
        if not isinstance(website, str) or not website:
            return None

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
        cache_candidates: set[str] = set()
        for url in urls:
            cache_candidates.update(self._post_cache_candidates(url))

        for candidate_url in cache_candidates:
            await delete_cached_file_payload(self._post_cache_key(candidate_url))

    async def _set_post_cache(self, source_url: str, post: MediaPost, media_payload: list[dict[str, Any]]) -> None:
        if not media_payload:
            return

        payload = self._build_post_cache_payload(post, media_payload)
        cache_candidates: set[str] = set()
        for url in (source_url, post.url):
            cache_candidates.update(self._post_cache_candidates(url))

        for candidate_url in cache_candidates:
            await set_cached_file_payload(self._post_cache_key(candidate_url), payload)

    async def _send_single_media(
        self, media: MediaItem, caption: str, keyboard: InlineKeyboardMarkup | None
    ) -> list[dict[str, Any]]:
        sent_message = None
        if media.kind == MediaKind.PHOTO:
            async with ChatActionSender.upload_photo(
                chat_id=self.event.chat.id, bot=self.bot, message_thread_id=self.event.message_thread_id
            ):
                try:
                    sent_message = await self.event.reply_photo(media.file, caption=caption, reply_markup=keyboard)
                except TelegramBadRequest as error:
                    if not self._is_missing_reply_error(error):
                        raise
                    sent_message = await self.bot.send_photo(
                        chat_id=self.event.chat.id,
                        photo=media.file,
                        caption=caption,
                        reply_markup=keyboard,
                        message_thread_id=self.event.message_thread_id,
                    )
        else:
            async with ChatActionSender.upload_video(
                chat_id=self.event.chat.id, bot=self.bot, message_thread_id=self.event.message_thread_id
            ):
                try:
                    sent_message = await self.event.reply_video(
                        media.file,
                        caption=caption,
                        reply_markup=keyboard,
                        duration=media.duration,
                        width=media.width,
                        height=media.height,
                        thumbnail=media.thumbnail,
                    )
                except TelegramBadRequest as error:
                    if not self._is_missing_reply_error(error):
                        raise
                    sent_message = await self.bot.send_video(
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

        if not sent_message:
            return []

        file_id = self._extract_sent_file_id(sent_message, media.kind)
        if not file_id:
            return []

        cache_key = make_file_id_cache_key("media-source", media.source_url)
        await set_cached_file_payload(cache_key, {"file_id": file_id})
        return [self._serialize_media_cache_entry(media, file_id)]

    async def _send_media_group(self, media_items: list[MediaItem], caption: str) -> list[dict[str, Any]]:
        builder = MediaGroupBuilder()
        last_index = len(media_items) - 1
        for index, item in enumerate(media_items):
            item_caption = caption if index == last_index else None
            if item.kind == MediaKind.PHOTO:
                builder.add_photo(item.file, caption=item_caption)
            else:
                builder.add_video(
                    item.file,
                    caption=item_caption,
                    duration=item.duration,
                    width=item.width,
                    height=item.height,
                    thumbnail=item.thumbnail,
                )

        media_group = builder.build()
        try:
            sent_messages = await self.bot.send_media_group(
                chat_id=self.event.chat.id,
                media=media_group,
                reply_to_message_id=self.event.message_id,
                message_thread_id=self.event.message_thread_id,
            )
        except TelegramBadRequest as error:
            if not self._is_missing_reply_error(error):
                raise
            sent_messages = await self.bot.send_media_group(
                chat_id=self.event.chat.id, media=media_group, message_thread_id=self.event.message_thread_id
            )

        cached_media_payload: list[dict[str, Any]] = []
        for item, sent in zip(media_items, sent_messages, strict=False):
            file_id = self._extract_sent_file_id(sent, item.kind)

            if not file_id:
                continue

            cache_key = make_file_id_cache_key("media-source", item.source_url)
            await set_cached_file_payload(cache_key, {"file_id": file_id})
            cached_media_payload.append(self._serialize_media_cache_entry(item, file_id))

        return cached_media_payload

    @classmethod
    def _format_caption(cls, post: MediaPost) -> str:
        return cls._build_caption(post, include_link=False)

    @classmethod
    def _format_caption_with_link(cls, post: MediaPost) -> str:
        return cls._build_caption(post, include_link=True)

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
        async with ChatActionSender.typing(
            chat_id=self.event.chat.id, bot=self.bot, message_thread_id=self.event.message_thread_id
        ):
            return await self.PROVIDER.fetch(url)

    async def _send_post(self, post: MediaPost) -> list[dict[str, Any]]:
        media_items = post.media[: self.MEDIA_GROUP_LIMIT]
        if not media_items:
            return []

        caption = self._format_caption(post)
        keyboard = self._build_keyboard(post)

        if len(media_items) == 1:
            cached_media_payload = await self._send_single_media(media_items[0], caption, keyboard)
            if len(cached_media_payload) != 1:
                return []
            return cached_media_payload

        group_caption = self._format_caption_with_link(post)
        async with ChatActionSender.upload_document(
            chat_id=self.event.chat.id, bot=self.bot, message_thread_id=self.event.message_thread_id
        ):
            cached_media_payload = await self._send_media_group(media_items, group_caption)

        if len(cached_media_payload) != len(media_items):
            return []
        return cached_media_payload

    async def handle(self) -> None:
        if not self.bot:
            return

        urls = cast("list[str]", self.data.get("media_urls") or [])
        if not urls:
            return

        source_url = urls[0]

        cached_post_payload = await self._get_cached_post(source_url)
        if cached_post_payload is not None:
            cached_url, cached_post = cached_post_payload
            try:
                cached_media_payload = await self._send_post(cached_post)
            except TelegramBadRequest:
                await self._delete_post_cache(source_url, cached_url, cached_post.url)
            else:
                if cached_media_payload:
                    await self._set_post_cache(source_url, cached_post, cached_media_payload)
                return

        post = await self._fetch_post(source_url)
        if not post:
            return

        cached_media_payload = await self._send_post(post)
        if not cached_media_payload:
            return

        await self._set_post_cache(source_url, post, cached_media_payload)

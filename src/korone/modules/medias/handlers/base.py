from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, cast

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import InlineKeyboardButton
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.media_group import MediaGroupBuilder
from stfu_tg import Bold, Code, Italic, Template, Url

from korone.filters.chat_status import GroupChatFilter
from korone.modules.medias.filters import MediaUrlFilter
from korone.modules.medias.utils.base import MediaKind
from korone.modules.utils_.file_id_cache import make_file_id_cache_key, set_cached_file_payload
from korone.modules.utils_.telegram_exceptions import REPLIED_NOT_FOUND
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import InlineKeyboardMarkup
    from stfu_tg.doc import Element

    from korone.modules.medias.utils.base import MediaItem, MediaPost, MediaProvider


class BaseMediaHandler(KoroneMessageHandler):
    CAPTION_LIMIT = 1024
    MEDIA_GROUP_LIMIT = 10

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

    async def _send_single_media(self, media: MediaItem, caption: str, keyboard: InlineKeyboardMarkup | None) -> None:
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
            return

        file_id: str | None = None
        if media.kind == MediaKind.PHOTO and sent_message.photo:
            file_id = sent_message.photo[-1].file_id
        elif media.kind == MediaKind.VIDEO and sent_message.video:
            file_id = sent_message.video.file_id

        if file_id:
            cache_key = make_file_id_cache_key("media-source", media.source_url)
            await set_cached_file_payload(cache_key, {"file_id": file_id})

    async def _send_media_group(self, media_items: list[MediaItem], caption: str) -> None:
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

        for item, sent in zip(media_items, sent_messages, strict=False):
            file_id: str | None = None
            if item.kind == MediaKind.PHOTO and sent.photo:
                file_id = sent.photo[-1].file_id
            elif item.kind == MediaKind.VIDEO and sent.video:
                file_id = sent.video.file_id

            if not file_id:
                continue

            cache_key = make_file_id_cache_key("media-source", item.source_url)
            await set_cached_file_payload(cache_key, {"file_id": file_id})

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

    async def handle(self) -> None:
        if not self.bot:
            return

        urls = cast("list[str]", self.data.get("media_urls") or [])
        if not urls:
            return

        post = await self.PROVIDER.fetch(urls[0])
        if not post:
            return

        media_items = post.media[: self.MEDIA_GROUP_LIMIT]

        caption = self._format_caption(post)
        keyboard = self._build_keyboard(post)

        if len(media_items) == 1:
            await self._send_single_media(media_items[0], caption, keyboard)
            return

        group_caption = self._format_caption_with_link(post)
        async with ChatActionSender.upload_document(
            chat_id=self.event.chat.id, bot=self.bot, message_thread_id=self.event.message_thread_id
        ):
            await self._send_media_group(media_items, group_caption)

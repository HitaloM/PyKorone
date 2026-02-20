from __future__ import annotations

from typing import TYPE_CHECKING, ClassVar, cast

from aiogram.types import InlineKeyboardButton
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.media_group import MediaGroupBuilder
from stfu_tg import Bold, Code, Italic, Template, Url

from korone.filters.chat_status import GroupChatFilter
from korone.modules.medias.filters import MediaUrlFilter
from korone.modules.medias.utils.base import MediaKind
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

    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:  # pyright: ignore[reportIncompatibleMethodOverride]
        return (GroupChatFilter(), MediaUrlFilter(cls.PROVIDER.pattern))

    async def _send_single_media(self, media: MediaItem, caption: str, keyboard: InlineKeyboardMarkup | None) -> None:
        if media.kind == MediaKind.PHOTO:
            async with ChatActionSender.upload_photo(
                chat_id=self.event.chat.id, bot=self.bot, message_thread_id=self.event.message_thread_id
            ):
                await self.event.reply_photo(media.file, caption=caption, reply_markup=keyboard)
                return

        async with ChatActionSender.upload_video(
            chat_id=self.event.chat.id, bot=self.bot, message_thread_id=self.event.message_thread_id
        ):
            await self.event.reply_video(
                media.file,
                caption=caption,
                reply_markup=keyboard,
                duration=media.duration,
                width=media.width,
                height=media.height,
                thumbnail=media.thumbnail,
            )

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

        await self.bot.send_media_group(
            chat_id=self.event.chat.id,
            media=builder.build(),
            reply_to_message_id=self.event.message_id,
            message_thread_id=self.event.message_thread_id,
        )

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

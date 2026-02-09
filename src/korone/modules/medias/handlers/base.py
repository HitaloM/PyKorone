from __future__ import annotations

from html import escape
from typing import TYPE_CHECKING, ClassVar, cast

from aiogram.types import InlineKeyboardButton
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.utils.media_group import MediaGroupBuilder

from korone.filters.chat_status import GroupChatFilter
from korone.modules.medias.filters import MediaUrlFilter
from korone.modules.medias.utils.base import MediaKind
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType
    from aiogram.types import InlineKeyboardMarkup

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
            async with ChatActionSender.upload_photo(chat_id=self.event.chat.id, bot=self.bot):
                await self.event.reply_photo(media.file, caption=caption, reply_markup=keyboard)
                return

        async with ChatActionSender.upload_video(chat_id=self.event.chat.id, bot=self.bot):
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
    def _build_caption(cls, post: MediaPost, *, include_link: bool) -> str:
        author_name = escape(post.author_name or cls.DEFAULT_AUTHOR_NAME)
        author_handle = escape(post.author_handle or cls.DEFAULT_AUTHOR_HANDLE)
        title = f"<b>{author_name}</b> (<code>{author_handle}</code>)"
        link = ""
        if include_link:
            link_text = escape(_("Open in {website}").format(website=post.website))
            link = f'\n\n<a href="{post.url}">{link_text}</a>'

        if not post.text:
            return f"{title}{link}"

        raw_text = post.text
        candidate = f"{title}\n\n<i>{escape(raw_text)}</i>{link}"
        if len(candidate) <= cls.CAPTION_LIMIT:
            return candidate

        trimmed_text = cls._truncate_text(raw_text, title, link)
        if not trimmed_text:
            return f"{title}{link}"

        return f"{title}\n\n<i>{escape(trimmed_text)}</i>{link}"

    @classmethod
    def _truncate_text(cls, raw_text: str, title: str, link: str) -> str:
        ellipsis = " [...]"
        low = 0
        high = len(raw_text)
        best = ""

        while low <= high:
            mid = (low + high) // 2
            truncated = raw_text[:mid].rstrip()
            text = f"{truncated}{ellipsis}" if truncated else ""
            candidate = f"{title}\n\n<i>{escape(text)}</i>{link}" if text else f"{title}{link}"

            if len(candidate) <= cls.CAPTION_LIMIT:
                best = text
                low = mid + 1
            else:
                high = mid - 1

        return best

    @staticmethod
    def _build_keyboard(post: MediaPost) -> InlineKeyboardMarkup | None:
        builder = InlineKeyboardBuilder()
        builder.add(InlineKeyboardButton(text=_("Open in {website}").format(website=post.website), url=post.url))
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
        async with ChatActionSender.upload_document(chat_id=self.event.chat.id, bot=self.bot):
            await self._send_media_group(media_items, group_caption)

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import re
from datetime import timedelta

from hairydogm.chat_action import ChatActionSender
from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram.client import Client
from hydrogram.enums import ChatAction
from hydrogram.types import InputMediaPhoto, InputMediaVideo, Message

from korone.decorators import router
from korone.filters import Regex
from korone.handlers.abstract import MessageHandler
from korone.modules.medias.utils.cache import MediaCache
from korone.modules.medias.utils.instagram import POST_PATTERN, instagram
from korone.utils.i18n import gettext as _

URL_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?instagram\.com/.*?(?=\s|$)")


class InstagramHandler(MessageHandler):
    @router.message(Regex(URL_PATTERN))
    async def handle(self, client: Client, message: Message) -> None:
        if not message.text:
            return

        url = self.extract_url(message.text)
        if not url:
            return

        media_list = await instagram(url)
        if not media_list:
            return

        if len(media_list) > 10:  # Telegram's limit
            last_caption = media_list[-1].caption
            media_list = media_list[:10]
            media_list[-1].caption = last_caption

        async with ChatActionSender(
            client=client, chat_id=message.chat.id, action=ChatAction.UPLOAD_DOCUMENT
        ):
            sent_message = await self.send_media(message, media_list, url)  # type: ignore

        post_id = self.extract_post_id(url)
        if post_id and sent_message:
            await self.cache_media(sent_message, post_id)

    @staticmethod
    def extract_url(text: str) -> str | None:
        if not text:
            return None

        match = URL_PATTERN.search(text)
        return match.group() if match else None

    async def send_media(
        self,
        message: Message,
        media_list: list[InputMediaPhoto | InputMediaVideo],
        url: str,
    ) -> Message | list[Message] | None:
        caption = self.build_caption(media_list, url)
        if len(media_list) == 1:
            return await self.send_single_media(message, media_list[0], caption, url)
        media_list[-1].caption = caption
        return await message.reply_media_group(media_list)

    @staticmethod
    def build_caption(media_list: list[InputMediaPhoto | InputMediaVideo], url: str) -> str:
        caption = media_list[-1].caption
        if len(media_list) > 1:
            caption += f"\n<a href='{url}'>{_("Open in Instagram")}</a>"
        return caption

    @staticmethod
    async def send_single_media(
        message: Message, media: InputMediaPhoto | InputMediaVideo, caption: str, url: str
    ) -> Message:
        keyboard = InlineKeyboardBuilder().button(text=_("Open in Instagram"), url=url).as_markup()
        if isinstance(media, InputMediaPhoto):
            return await message.reply_photo(media.media, caption=caption, reply_markup=keyboard)
        if isinstance(media, InputMediaVideo):
            return await message.reply_video(media.media, caption=caption, reply_markup=keyboard)
        return None

    @staticmethod
    def extract_post_id(url: str) -> str | None:
        match = POST_PATTERN.search(url)
        return match.group(1) if match else None

    @staticmethod
    async def cache_media(message: Message | list[Message], post_id: str) -> None:
        cache = MediaCache(post_id)
        await cache.set(message, expire=int(timedelta(weeks=1).total_seconds()))

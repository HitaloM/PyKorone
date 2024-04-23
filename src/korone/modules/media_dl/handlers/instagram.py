# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

import re
from datetime import timedelta

import aiohttp
from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.types import InputMediaPhoto, InputMediaVideo, Message
from magic_filter import F

from korone import cache
from korone.decorators import router
from korone.handlers.message_handler import MessageHandler
from korone.modules.utils.filters.magic import Magic
from korone.utils.i18n import gettext as _


class InstagramHandler(MessageHandler):
    def __init__(self) -> None:
        self.url_pattern = re.compile(
            r"(?:https?:\/\/)?(?:www\.)?instagram\.com\/(?:p|reels)\/([^/?#&]+).*"
        )
        self.image_pattern = re.compile(r"(.+\.jpg)")
        self.video_pattern = re.compile(r"(.+\.mp4)")

    @staticmethod
    @cache(ttl=timedelta(days=1))
    async def fetch_data(url: str):
        async with aiohttp.ClientSession() as session:
            response = await session.get(url)
            if response.status != 200:
                return None
            return response.url.human_repr()

    @router.message(
        Magic(
            F.text.regexp(r"((?:https?:\/\/)?(?:www\.)?instagram\.com\/(?:p|reels)\/([^/?#&]+)).*")
        )
    )
    async def handle(self, client: Client, message: Message) -> None:
        url = self.url_pattern.search(message.text)
        if not url:
            return

        post_id = url.group(1)
        dd_url = f"https://ddinstagram.com/images/{post_id}/"

        url_list = []
        for i in range(1, 11):
            data = await self.fetch_data(dd_url + str(i))
            if data is None:
                break
            url_list.append(data)

        if not url_list:
            return

        keyboard = InlineKeyboardBuilder()
        keyboard.button(text=_("Open in Instagram"), url=url.group())

        if len(url_list) == 1:
            media = url_list[0]
            if re.search(self.image_pattern, media):
                await message.reply_photo(media, reply_markup=keyboard.as_markup())
            elif re.search(self.video_pattern, media):
                await message.reply_video(media, reply_markup=keyboard.as_markup())
            return

        media_list = []
        for media in url_list:
            if re.search(self.image_pattern, media):
                media_list.append(InputMediaPhoto(media))
            elif re.search(self.video_pattern, media):
                media_list.append(InputMediaVideo(media))

        if not media_list:
            return

        media_list[-1].caption = f"<a href='{url.group()}'>{_("Open in Instagram")}</a>"
        await message.reply_media_group(media_list)

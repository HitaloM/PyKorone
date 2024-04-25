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
            r"((?:https?:\/\/)?(?:www\.)?instagram\.com\/(?:p|reels|reel)\/([^/?#&]+)).*"
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
            F.text.regexp(
                r"(?:https?:\/\/)?(?:www\.)?instagram\.com\/(?:p|reels|reel)\/([^/?#&]+).*"
            )
        )
    )
    async def handle(self, client: Client, message: Message) -> None:
        post_url = self.url_pattern.search(message.text)
        if not post_url:
            return

        post_id = post_url.group(2)
        if not post_id:
            return
        if not re.match(r"^[A-Za-z0-9\-_]+$", post_id):
            return

        dd_url = f"https://ddinstagram.com/images/{post_id}/"

        url_list: list[str] = []
        for i in range(1, 11):
            url = await self.fetch_data(dd_url + str(i))
            if not url:
                break
            url_list.append(url)

        if not url_list:
            return

        if len(url_list) == 1:
            url = url_list[0]

            keyboard = InlineKeyboardBuilder()
            keyboard.button(text=_("Open in Instagram"), url=post_url.group())

            if re.search(self.image_pattern, url):
                await message.reply_photo(url, reply_markup=keyboard.as_markup())
            elif re.search(self.video_pattern, url):
                await message.reply_video(url, reply_markup=keyboard.as_markup())
            return

        media_list: list[InputMediaPhoto | InputMediaVideo] = []
        for media in url_list:
            if re.search(self.image_pattern, media):
                media_list.append(InputMediaPhoto(media))
            elif re.search(self.video_pattern, media):
                media_list.append(InputMediaVideo(media))

        if not media_list:
            return

        media_list[-1].caption = f"<a href='{post_url.group()}'>{_("Open in Instagram")}</a>"
        await message.reply_media_group(media_list)

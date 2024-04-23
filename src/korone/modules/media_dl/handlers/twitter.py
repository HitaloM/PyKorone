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


class TwitterHandler(MessageHandler):
    def __init__(self):
        self.url_pattern = re.compile(r"https?://(?:www\.)?(twitter\.com|x\.com)/.+?/status/\d+")
        self.img_pattern = re.compile(r"\.(jpg|jpeg|png)")
        self.vid_pattern = re.compile(r"\.(mp4|webm)")

    @staticmethod
    @cache(ttl=timedelta(hours=1))
    async def fetch_data(url: str) -> dict | None:
        async with aiohttp.ClientSession() as session:
            response = await session.get(url)
            if response.status != 200:
                return None
            return await response.json()

    @staticmethod
    async def parse_data(data: dict) -> dict:
        return {
            "mediaURLs": data.get("mediaURLs", []),
            "text": data.get("text", ""),
            "user_name": data.get("user_name", ""),
            "tweetURL": data.get("tweetURL", ""),
        }

    @router.message(
        Magic(F.text.regexp(r"https?://(?:www\.)?(twitter\.com|x\.com)/.+?/status/\d+"))
    )
    async def handle(self, client: Client, message: Message) -> None:
        url = self.url_pattern.search(message.text)
        if not url:
            return

        vx_url = re.sub(r"(www\.|)(twitter\.com|x\.com)", "api.vxtwitter.com", url.group())
        data = await self.fetch_data(vx_url)
        if not data:
            return

        data = await self.parse_data(data)

        text = f"<b>{data["user_name"]}:</b>\n\n"
        text += data["text"]

        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="Open in Twitter", url=data["tweetURL"])

        media_urls = data["mediaURLs"]
        if len(media_urls) == 1:
            text = re.sub(r"https?://t\.co/\S*", "", text)
            if isinstance(media_urls[0], InputMediaVideo):
                await message.reply_video(
                    media_urls[0], caption=text, reply_markup=keyboard.as_markup()
                )
            else:
                await message.reply_photo(
                    media_urls[0], caption=text, reply_markup=keyboard.as_markup()
                )
            return

        media_list = []
        for media in media_urls:
            if re.search(self.img_pattern, media):
                if re.search(self.vid_pattern, media):
                    media_list.append(InputMediaVideo(media))
                else:
                    media_list.append(InputMediaPhoto(media))

        if not media_list:
            return

        media_list[-1].caption = text
        await message.reply_media_group(media=media_list)

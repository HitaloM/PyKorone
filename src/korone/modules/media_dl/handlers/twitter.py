# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

import re
from datetime import timedelta

import aiohttp
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
        self.media_pattern = re.compile(r"\.(mp4|jpg|jpeg|png)")

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

        if len(data["mediaURLs"]) == 1:
            if re.search(r"\.mp4", data["mediaURLs"][0]):
                await message.reply_video(data["mediaURLs"][0], caption=text)
            return

        media_list = [
            InputMediaVideo(media) if re.search(r"\.mp4", media) else InputMediaPhoto(media)
            for media in data["mediaURLs"]
            if re.search(self.media_pattern, media)
        ]

        if not media_list:
            return

        media_list[-1].caption = text

        await message.reply_media_group(media=media_list)

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

import io
import re
from dataclasses import dataclass
from datetime import timedelta

import aiohttp
import orjson
from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.types import InputMediaPhoto, InputMediaVideo, Message
from magic_filter import F

from korone.decorators import router
from korone.handlers.message_handler import MessageHandler
from korone.modules.utils.filters.magic import Magic
from korone.utils.i18n import gettext as _


@dataclass(frozen=True, slots=True)
class SizeData:
    height: int
    width: int


@dataclass(frozen=True, slots=True)
class MediaData:
    alt_text: str
    size: SizeData
    thumbnail_url: str
    type: str
    url: str
    duration_millis: int


@dataclass(frozen=True, slots=True)
class TweetData:
    community_note: str
    conversation_id: str
    date: str
    date_epoch: int
    hashtags: list[str]
    likes: int
    media_urls: list[str]
    media_extended: list[MediaData]
    possibly_sensitive: bool
    qrt_url: str
    replies: int
    retweets: int
    text: str
    tweet_id: str
    tweet_url: str
    user_name: str
    user_profile_image_url: str
    user_screen_name: str


class TwitterHandler(MessageHandler):
    def __init__(self):
        self.url_pattern = re.compile(
            r"(?:(?:http|https):\/\/)?(?:www.)?(twitter\.com|x\.com)/.+?/status/\d+"
        )

    @staticmethod
    async def fetch_data(url: str) -> dict | None:
        async with aiohttp.ClientSession() as session:
            response = await session.get(url)
            if response.status != 200:
                return None
            return await response.json(loads=orjson.loads)

    @staticmethod
    async def parse_data(data: dict) -> TweetData:
        media_extended = [
            MediaData(
                alt_text=media.get("altText"),
                size=SizeData(**media.get("size")),
                thumbnail_url=media.get("thumbnail_url"),
                type=media.get("type"),
                url=media.get("url"),
                duration_millis=media.get("duration_millis"),
            )
            for media in data.get("media_extended", [])
        ]

        return TweetData(
            community_note=data.get("communityNote", ""),
            conversation_id=data.get("conversationID", ""),
            date=data.get("date", ""),
            date_epoch=data.get("date_epoch", ""),
            hashtags=data.get("hashtags", ""),
            likes=data.get("likes", ""),
            media_urls=data.get("mediaURLs", ""),
            media_extended=media_extended,
            possibly_sensitive=data.get("possibly_sensitive", ""),
            qrt_url=data.get("qrtURL", ""),
            replies=data.get("replies", ""),
            retweets=data.get("retweets", ""),
            text=data.get("text", ""),
            tweet_id=data.get("tweetID", ""),
            tweet_url=data.get("tweetURL", ""),
            user_name=data.get("user_name", ""),
            user_profile_image_url=data.get("user_profile_image_url", ""),
            user_screen_name=data.get("user_screen_name", ""),
        )

    async def url_to_binary_io(self, url: str) -> io.BytesIO:
        async with aiohttp.ClientSession() as session:
            session = await session.get(url)
            content = await session.read()
            file = io.BytesIO(content)
            file.name = url.split("/")[-1]
            return file

    @router.message(
        Magic(
            F.text.regexp(r"(?:(?:http|https):\/\/)?(?:www.)?(twitter\.com|x\.com)/.+?/status/\d+")
        )
    )
    async def handle(self, client: Client, message: Message) -> None:
        url = self.url_pattern.search(message.text)
        if not url:
            return

        vx_url = re.sub(r"(www\.|)(twitter\.com|x\.com)", "api.vxtwitter.com", url.group())
        data = await self.fetch_data(vx_url)
        if not data:
            return

        tweet = await self.parse_data(data)

        text = f"<b>{tweet.user_name} (<code>@{tweet.user_screen_name}</code>):</b>\n\n"
        text += tweet.text

        if len(tweet.media_extended) == 1:
            text = re.sub(r"https?://t\.co/\S*", "", text)
            media = tweet.media_extended[0]

            keyboard = InlineKeyboardBuilder()
            keyboard.button(text=_("Open in Twitter"), url=tweet.tweet_url)

            media_url = await self.url_to_binary_io(media.url)
            if media.type == "image":
                await client.send_photo(
                    chat_id=message.chat.id,
                    photo=media_url,
                    caption=text,
                    reply_markup=keyboard.as_markup(),
                    reply_to_message_id=message.id,
                )
            elif media.type in {"video", "gif"}:
                media_thumb = await self.url_to_binary_io(media.thumbnail_url)
                await client.send_video(
                    chat_id=message.chat.id,
                    video=media_url,
                    caption=text,
                    reply_markup=keyboard.as_markup(),
                    duration=int(
                        timedelta(milliseconds=media.duration_millis).total_seconds() * 1000
                    ),
                    width=media.size.width,
                    height=media.size.height,
                    thumb=media_thumb,
                    reply_to_message_id=message.id,
                )
            return

        media_list: list[InputMediaPhoto | InputMediaVideo] = []
        for media in tweet.media_extended:
            media_url = await self.url_to_binary_io(media.url)
            if media.type == "image":
                media_list.append(InputMediaPhoto(media_url))
            if media.type in {"video", "gif"}:
                media_thumb = await self.url_to_binary_io(media.thumbnail_url)
                media_list.append(
                    InputMediaVideo(
                        media=media_url,
                        duration=int(
                            timedelta(milliseconds=media.duration_millis).total_seconds() * 1000
                        ),
                        width=media.size.width,
                        height=media.size.height,
                        thumb=media_thumb,  # type: ignore
                    )
                )

        if not media_list:
            return

        media_list[-1].caption = text
        await message.reply_media_group(media=media_list)

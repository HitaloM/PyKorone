# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import io
import re
from dataclasses import dataclass
from typing import BinaryIO

import httpx
import orjson

from korone.utils.logging import log


class TwitterError(Exception):
    pass


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
    binary_io: BinaryIO
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


class VxTwitterAPI:
    __slots__ = ("http_client", "tweet_data")

    def __init__(self):
        self.tweet_data: TweetData
        self.http_client = httpx.AsyncClient(http2=True)

    @staticmethod
    def convert_to_vx_url(url: str) -> str:
        return re.sub(r"(www\.|)(twitter\.com|x\.com)", "api.vxtwitter.com", url)

    async def fetch(self, url: str) -> TweetData | None:
        vx_url = self.convert_to_vx_url(url)
        try:
            response = await self.http_client.get(vx_url)
            response.raise_for_status()
        except httpx.HTTPStatusError as err:
            log.error("Error fetching tweet data: %s", err)
            raise TwitterError from err

        data = orjson.loads(response.text)
        self.tweet_data = await self.parse_data(data)
        return self.tweet_data

    async def parse_data(self, data: dict) -> TweetData:
        media_extended = [
            MediaData(
                alt_text=media.get("altText"),
                size=SizeData(**media.get("size")),
                thumbnail_url=media.get("thumbnail_url"),
                type=media.get("type"),
                binary_io=await self.url_to_binary_io(media.get("url")),
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

    async def url_to_binary_io(self, url: str) -> BinaryIO:
        try:
            response = await self.http_client.get(url)
            response.raise_for_status()
            content = response.read()
        except httpx.HTTPStatusError as e:
            print(f"Error fetching binary data: {e}")
            return io.BytesIO()

        file = io.BytesIO(content)
        file.name = url.split("/")[-1]
        return file

    def __getattr__(self, name):
        if self.tweet_data is not None and hasattr(self.tweet_data, name):
            return getattr(self.tweet_data, name)

        msg = f"'{type(self).__name__}' object has no attribute '{name}'"
        raise AttributeError(msg)

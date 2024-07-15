# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import io
import re
from dataclasses import dataclass
from datetime import timedelta
from typing import BinaryIO

import httpx

from korone import cache
from korone.utils.logging import logger


class TwitterError(Exception):
    pass


@dataclass(frozen=True, slots=True)
class TweetAuthor:
    name: str
    screen_name: str


@dataclass(frozen=True, slots=True)
class TweetMediaVariants:
    content_type: str
    bitrate: int
    url: str
    binary_io: BinaryIO


@dataclass(frozen=True, slots=True)
class TweetMedia:
    type: str
    format: str
    url: str
    binary_io: BinaryIO
    duration: int
    width: int
    height: int
    thumbnail_io: BinaryIO | None
    thumbnail_url: str
    variants: list[TweetMediaVariants]


@dataclass(frozen=True, slots=True)
class TweetData:
    url: str
    text: str
    author: TweetAuthor
    replies: int
    retweets: int
    likes: int
    created_at_timestamp: int
    media: list[TweetMedia]
    source: str


class TwitterAPI:
    __slots__ = ("tweet", "url")

    def __init__(self, url: str):
        self.url = url
        self.tweet: TweetData | None = None

    async def fetch_and_parse(self) -> None:
        data = await self._fetch(self.url)
        self.tweet = await self._parse_data(data)

    @staticmethod
    def _convert_to_fx_url(url: str) -> str:
        return re.sub(r"(www\.|)(twitter\.com|x\.com)", "api.fxtwitter.com", url)

    @cache(ttl=timedelta(weeks=1), key="tweet_data:{url}")
    async def _fetch(self, url: str) -> dict:
        fx_url = self._convert_to_fx_url(url)
        try:
            async with httpx.AsyncClient(http2=True) as client:
                response = await client.get(fx_url)
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as err:
            logger.error(f"Error fetching tweet data: {err}")
            raise TwitterError from err

    async def _parse_data(self, data: dict) -> TweetData:
        tweet = data.get("tweet", {})
        medias = tweet.get("media", {}).get("all", [])
        author = tweet.get("author", {})

        media = [await self._create_tweet_media(media) for media in medias]

        return TweetData(
            url=tweet.get("url", ""),
            text=tweet.get("text", ""),
            author=TweetAuthor(
                name=author.get("name", ""),
                screen_name=author.get("screen_name", ""),
            ),
            replies=tweet.get("replies", 0),
            retweets=tweet.get("retweets", 0),
            likes=tweet.get("likes", 0),
            created_at_timestamp=tweet.get("created_at_timestamp", 0),
            media=media,
            source=tweet.get("source", ""),
        )

    async def _create_tweet_media(self, media: dict) -> TweetMedia:
        variants = [
            await self._create_tweet_media_variant(variant)
            for variant in media.get("variants", [])
        ]
        thumbnail_io = None
        if thumbnail_url := media.get("thumbnail_url"):
            thumbnail_io = await self._url_to_binary_io(thumbnail_url)

        binary_io = await self._url_to_binary_io(media.get("url", ""))

        return TweetMedia(
            type=media.get("type", ""),
            format=media.get("format", ""),
            url=media.get("url", ""),
            binary_io=binary_io,
            duration=media.get("duration", 0),
            width=media.get("width", 0),
            height=media.get("height", 0),
            thumbnail_io=thumbnail_io,
            thumbnail_url=media.get("thumbnail_url", ""),
            variants=variants,
        )

    async def _create_tweet_media_variant(self, variant: dict) -> TweetMediaVariants:
        return TweetMediaVariants(
            content_type=variant.get("content_type", ""),
            bitrate=variant.get("bitrate", 0),
            url=variant.get("url", ""),
            binary_io=await self._url_to_binary_io(variant.get("url", "")),
        )

    @staticmethod
    @cache(ttl=timedelta(weeks=1), key="tweet_binary:{url}")
    async def _url_to_binary_io(url: str) -> BinaryIO:
        try:
            async with httpx.AsyncClient(http2=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                content = await response.aread()
        except httpx.HTTPError as err:
            logger.error(f"Error fetching media data: {err}")
            raise TwitterError from err

        file = io.BytesIO(content)
        file.name = url.split("/")[-1]
        return file

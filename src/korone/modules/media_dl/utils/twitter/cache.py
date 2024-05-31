# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import pickle

from cashews.exceptions import CacheError
from hydrogram.types import Message

from korone import cache
from korone.modules.media_dl.utils.twitter.api import TweetData
from korone.utils.logging import log


class TwitterCache:
    __slots__ = ("key",)

    def __init__(self, tweet: TweetData) -> None:
        self.key = f"tweet:{tweet.url}:media"

    @staticmethod
    def _serialize_photo(message: Message) -> dict:
        return {"photo": {"file": message.photo.file_id}}

    @staticmethod
    def _serialize_video(message: Message) -> dict:
        thumbnail = message.video.thumbs[0].file_id if message.video.thumbs else None
        return {
            "video": {
                "file": message.video.file_id,
                "duration": message.video.duration,
                "width": message.video.width,
                "height": message.video.height,
                "thumbnail": thumbnail,
            }
        }

    def serialize_media_dict(self, sent: Message | list[Message]) -> dict:
        media_dict = {}
        messages = sent if isinstance(sent, list) else [sent]

        for m in messages:
            if m.photo:
                media_dict[m.photo.file_id] = self._serialize_photo(m)
            elif m.video:
                media_dict[m.video.file_id] = self._serialize_video(m)

        return media_dict

    async def get(self) -> dict | None:
        try:
            cache_data = await cache.get(self.key)
            if cache_data:
                return pickle.loads(cache_data)
        except CacheError as e:
            log.exception("Failed to get data from cache: %s", e)
        return None

    async def set(self, value: Message | list[Message], expire: int) -> None:
        serialized_data = self.serialize_media_dict(value)
        try:
            serialized_cache = pickle.dumps(serialized_data)
            await cache.set(self.key, serialized_cache, expire=expire)
        except CacheError as e:
            log.exception("Failed to set data to cache: %s", e)

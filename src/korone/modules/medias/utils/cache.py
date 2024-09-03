# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import pickle
from typing import Any

from cashews.exceptions import CacheError
from hydrogram.types import Message

from korone.utils.caching import cache
from korone.utils.logging import logger


class MediaCache:
    __slots__ = ("key",)

    def __init__(self, identifier: Any) -> None:
        self.key = f"media-cache:{identifier}:media"

    @staticmethod
    def _serialize_photo(message: Message) -> dict:
        return {"file": message.photo.file_id}

    @staticmethod
    def _serialize_video(message: Message) -> dict:
        thumbnail = message.video.thumbs[0].file_id if message.video.thumbs else None
        return {
            "file": message.video.file_id,
            "duration": message.video.duration,
            "width": message.video.width,
            "height": message.video.height,
            "thumbnail": thumbnail,
        }

    def serialize_media_dict(self, sent: Message | list[Message]) -> dict:
        media_dict = {"photo": [], "video": []}
        messages = sent if isinstance(sent, list) else [sent]

        for m in messages:
            if m.photo:
                media_dict["photo"].append(self._serialize_photo(m))
            elif m.video:
                media_dict["video"].append(self._serialize_video(m))

        return media_dict

    async def get(self) -> dict | None:
        try:
            cache_data = await cache.get(self.key)
            if cache_data:
                return pickle.loads(cache_data)
        except CacheError as e:
            await logger.aexception("[Medias/Cache] Failed to get data from cache: %s", e)
        return None

    async def set(self, value: Message | list[Message], expire: int) -> None:
        serialized_data = self.serialize_media_dict(value)
        try:
            serialized_cache = pickle.dumps(serialized_data)
            await cache.set(self.key, serialized_cache, expire=expire)
        except CacheError as e:
            await logger.aexception("[Medias/Cache] Failed to set data to cache: %s", e)

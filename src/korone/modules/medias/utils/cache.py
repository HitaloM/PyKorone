# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import pickle
from typing import Any

from cashews.exceptions import CacheError
from hydrogram.types import InputMediaPhoto, InputMediaVideo, Message

from korone.utils.caching import cache
from korone.utils.logging import get_logger

logger = get_logger(__name__)


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

    @staticmethod
    def _convert_to_input_media(media_dict: dict) -> list[InputMediaPhoto | InputMediaVideo]:
        return [InputMediaPhoto(media["file"]) for media in media_dict.get("photo", [])] + [
            InputMediaVideo(
                media=media["file"],
                duration=media["duration"],
                width=media["width"],
                height=media["height"],
                thumb=media["thumbnail"],
            )
            for media in media_dict.get("video", [])
        ]

    async def get(self) -> list[InputMediaPhoto | InputMediaVideo] | None:
        try:
            cache_data = await cache.get(self.key)
            if cache_data:
                media_dict = pickle.loads(cache_data)
                return self._convert_to_input_media(media_dict)
        except CacheError as e:
            await logger.aexception("[Medias/Cache] Get failed: %s", e)
        return None

    async def set(self, value: Message | list[Message], expire: int) -> None:
        serialized_data = self.serialize_media_dict(value)
        try:
            serialized_cache = pickle.dumps(serialized_data)
            await cache.set(self.key, serialized_cache, expire=expire)
        except CacheError as e:
            await logger.aexception("[Medias/Cache] Set failed: %s", e)

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from datetime import timedelta
from pathlib import Path

import httpx

from korone import cache
from korone.modules.medias.utils.tiktok.types import TikTokSlideshow, TikTokVideo
from korone.utils.logging import logger


class TikTokError(Exception):
    pass


class TikTokClient:
    __slots__ = ("files_path", "media_id")

    def __init__(self, media_id: str):
        self.media_id = media_id
        self.files_path = []

    @staticmethod
    async def _request(method: str, url: str, **kwargs) -> httpx.Response:
        async with httpx.AsyncClient(http2=True) as client:
            try:
                response = await client.request(method=method, url=url, **kwargs)
                response.raise_for_status()
                return response
            except httpx.HTTPStatusError as e:
                msg = f"HTTP error: {e.response.status_code}"
                raise TikTokError(msg) from e
            except httpx.RequestError as e:
                msg = f"Request error: {e.request.url}"
                raise TikTokError(msg) from e

    @cache(ttl=timedelta(weeks=1), key="tiktok_data:{media_id}")
    async def _fetch_tiktok_data(self, media_id: str) -> dict:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; "
            "Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0"
        }
        params = {
            "iid": "7318518857994389254",
            "device_id": "7318517321748022790",
            "channel": "googleplay",
            "version_code": "300904",
            "device_platform": "android",
            "device_type": "ASUS_Z01QD",
            "os_version": "9",
            "aweme_id": media_id,
            "aid": "1128",
        }

        api_response = await self._request(
            "OPTIONS",
            "https://api16-normal-c-useast1a.tiktokv.com/aweme/v1/feed/",
            headers=headers,
            params=params,
        )

        return api_response.json() if api_response.status_code == 200 else {}

    @staticmethod
    async def _process_slideshow(aweme: dict, aweme_dict: dict) -> TikTokSlideshow:
        images = [
            image["display_image"]["url_list"][0] for image in aweme["image_post_info"]["images"]
        ]
        music_url = aweme["music"]["play_url"]["uri"]
        aweme_dict.update({"images": images, "music_url": music_url})

        return TikTokSlideshow(**aweme_dict)

    @staticmethod
    async def _process_video(aweme: dict, aweme_dict: dict) -> TikTokVideo:
        return TikTokVideo(
            author=aweme_dict["author"],
            desc=aweme_dict["desc"],
            width=aweme["video"]["play_addr"]["width"],
            height=aweme["video"]["play_addr"]["height"],
            duration=aweme["video"]["duration"],
            video_url=aweme["video"]["play_addr"]["url_list"][0],
            thumbnail_url=aweme["video"]["cover"]["url_list"][0],
        )

    async def get(self) -> TikTokSlideshow | TikTokVideo | None:
        tiktok_data = await self._fetch_tiktok_data(self.media_id)
        if not tiktok_data.get("aweme_list"):
            return None

        aweme = tiktok_data["aweme_list"][0]
        aweme_dict = {
            "author": aweme["author"]["nickname"]
            if aweme.get("author") and aweme["author"].get("nickname")
            else None,
            "desc": aweme.get("desc"),
        }

        if aweme.get("aweme_type") in {2, 68, 150}:
            return await self._process_slideshow(aweme, aweme_dict)
        return await self._process_video(aweme, aweme_dict)

    def clear(self) -> None:
        for path in self.files_path:
            if path and Path(path).exists():
                Path(path).unlink(missing_ok=True)
                logger.debug("Removed file %s", path)

        self.files_path.clear()

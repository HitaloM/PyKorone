# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import re
from datetime import timedelta
from typing import BinaryIO, cast

import httpx
from anyio import create_task_group, to_thread
from hydrogram.types import InputMediaPhoto, InputMediaVideo

from korone.modules.medias.utils.downloader import download_media
from korone.modules.medias.utils.files import resize_thumbnail
from korone.modules.medias.utils.generic_headers import GENERIC_HEADER
from korone.utils.caching import cache

from .types import TikTokSlideshow, TikTokVideo

URL_PATTERN = re.compile(
    r"""https:\/\/
    (?:(?:m|www|vm|vt)\.)?
    (?:
        tiktok\.com|
        vxtiktok\.com|
        tfxktok\.com
    )
    \/
    (
        (?:
            .*?\b(?:
                usr|v|embed|user|video|photo
            )\/|
            \?shareId=|
            \&item_id=
        )
        (\d+)
    |
        \w+
    )
    """,
    re.VERBOSE | re.IGNORECASE,
)


class TikTokError(Exception):
    pass


async def request_tiktok(method: str, url: str, **kwargs) -> httpx.Response:
    async with httpx.AsyncClient(http2=True) as client:
        try:
            response = await client.request(method=method, url=url, **kwargs)
            response.raise_for_status()
            return response
        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            msg = f"[Medias/TikTok] - Failed to fetch data: {e}"
            raise TikTokError(msg) from e


@cache(ttl=timedelta(weeks=1), key="tiktok_data:{media_id}")
async def fetch_tiktok_data(media_id: str) -> dict:
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
    response = await request_tiktok(
        "OPTIONS",
        "https://api16-normal-c-useast1a.tiktokv.com/aweme/v1/feed/",
        headers=GENERIC_HEADER,
        params=params,
    )
    return response.json() if response.status_code == 200 else {}


def process_slideshow(aweme: dict, data: dict) -> TikTokSlideshow:
    data["images"] = [
        img["display_image"]["url_list"][0] for img in aweme["image_post_info"]["images"]
    ]
    data["music_url"] = aweme["music"]["play_url"]["uri"]
    return TikTokSlideshow(**data)


def process_video(aweme: dict, data: dict) -> TikTokVideo:
    return TikTokVideo(
        author=data["author"],
        desc=data["desc"],
        width=aweme["video"]["play_addr"]["width"],
        height=aweme["video"]["play_addr"]["height"],
        duration=aweme["video"]["duration"],
        video_url=aweme["video"]["play_addr"]["url_list"][0],
        thumbnail_url=aweme["video"]["cover"]["url_list"][0],
    )


async def get_tiktok_media_by_id(media_id: str) -> TikTokSlideshow | TikTokVideo | None:
    tiktok_data = await fetch_tiktok_data(media_id)
    aweme_list = tiktok_data.get("aweme_list")
    if not aweme_list:
        return None

    aweme = aweme_list[0]
    if aweme.get("aweme_id") != media_id:
        return None

    data = {
        "author": aweme.get("author", {}).get("nickname"),
        "desc": aweme.get("desc"),
    }
    return (
        process_slideshow(aweme, data)
        if aweme.get("aweme_type") in {2, 68, 150}
        else process_video(aweme, data)
    )


async def safe_download(url: str) -> BinaryIO:
    result = await download_media(url)
    if not result:
        msg = f"[Medias/TikTok] - Failed to download media from {url}"
        raise TikTokError(msg)
    return result


async def prepare_video_media(media: TikTokVideo) -> InputMediaVideo:
    video_file: BinaryIO | None = None
    thumb_file: BinaryIO | None = None

    async def fetch_video() -> None:
        nonlocal video_file
        video_file = await safe_download(str(media.video_url))

    async def fetch_thumbnail() -> None:
        nonlocal thumb_file
        thumb_file = await safe_download(str(media.thumbnail_url))

    async with create_task_group() as tg:
        tg.start_soon(fetch_video)
        tg.start_soon(fetch_thumbnail)

    if not video_file or not thumb_file:
        msg = "[Medias/TikTok] - Failed to download video or thumbnail"
        raise TikTokError(msg)

    await to_thread.run_sync(resize_thumbnail, thumb_file)
    return InputMediaVideo(
        media=video_file,
        duration=media.duration,
        width=media.width,
        height=media.height,
        thumb=thumb_file,
    )


async def prepare_slideshow_media(media: TikTokSlideshow) -> list[InputMediaPhoto]:
    results: list[BinaryIO | None] = [None] * len(media.images)

    async def fetch_image(index: int, url: str) -> None:
        results[index] = await safe_download(url)

    async with create_task_group() as tg:
        for index, url in enumerate(media.images):
            tg.start_soon(fetch_image, index, str(url))

    return [InputMediaPhoto(media=cast(BinaryIO, result)) for result in results if result]


async def extract_media_id(url_match: re.Match[str]) -> int | None:
    media_id_str = url_match.group(2) or url_match.group(1)
    try:
        return int(media_id_str)
    except ValueError:
        redirect = await resolve_redirect_url(url_match.group(0))
        if redirect:
            match = URL_PATTERN.search(redirect)
            if match:
                try:
                    return int(match.group(2))
                except (TypeError, ValueError):
                    pass
        return None


async def resolve_redirect_url(url: str) -> str | None:
    try:
        async with httpx.AsyncClient(
            http2=True,
            timeout=20,
            follow_redirects=True,
            headers=GENERIC_HEADER,
        ) as client:
            response = await client.head(url)
            return str(response.url) if response.url else None
    except (httpx.RequestError, httpx.HTTPStatusError):
        return None


async def fetch_tiktok_media(tiktok_url: str):
    url_match = URL_PATTERN.search(tiktok_url)
    if not url_match:
        return None

    media_id = await extract_media_id(url_match)
    if not media_id:
        return None

    try:
        media_obj = await get_tiktok_media_by_id(str(media_id))
        if not media_obj:
            return None

        if isinstance(media_obj, TikTokVideo):
            media = await prepare_video_media(media_obj)
            mtype = "video"
        else:
            media = await prepare_slideshow_media(media_obj)
            mtype = "slideshow"

        return media, mtype, str(media_id), media_obj
    except TikTokError:
        return None

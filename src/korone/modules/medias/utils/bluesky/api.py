# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from __future__ import annotations

import html
import re
from datetime import timedelta
from typing import TYPE_CHECKING
from urllib.parse import urljoin

import httpx
import m3u8
from anyio import create_task_group
from cashews import NOT_NONE
from hydrogram.types import InputMediaPhoto, InputMediaVideo
from pydantic import HttpUrl, ValidationError

from korone.modules.medias.utils.cache import MediaCache
from korone.modules.medias.utils.downloader import download_media
from korone.modules.medias.utils.files import resize_thumbnail
from korone.utils.caching import cache
from korone.utils.concurrency import run_blocking
from korone.utils.logging import get_logger

from .types import BlueskyData, Image

if TYPE_CHECKING:
    from io import BytesIO

    from korone.modules.medias.utils.common import MediaGroupItem

logger = get_logger(__name__)


async def fetch_bluesky(text: str) -> list[MediaGroupItem] | None:
    username, post_id = get_username_and_post_id(text)
    if not post_id:
        return None

    bluesky_data = await get_bluesky_data(username, post_id)
    if not bluesky_data:
        return None

    caption = get_caption(bluesky_data)

    cache = MediaCache(post_id)
    if cached_data := await cache.get():
        cached_data[-1].caption = caption
        return cached_data

    media_list = await process_media(bluesky_data)

    if not media_list:
        return None

    media_list[-1].caption = caption

    return media_list


def get_username_and_post_id(url: str):
    if match := re.search(r"([^/?#]+)/post/([A-Za-z0-9_-]+)", url):
        return match[1], match[2]
    return None, None


@cache(ttl=timedelta(weeks=1), condition=NOT_NONE)
async def get_bluesky_data(username: str | None, post_id: str) -> BlueskyData | None:
    url = "https://public.api.bsky.app/xrpc/app.bsky.feed.getPostThread"
    params = {"uri": f"at://{username}/app.bsky.feed.post/{post_id}", "depth": "0"}
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    }

    async with httpx.AsyncClient(http2=True, timeout=20) as client:
        response = await client.get(url, headers=headers, params=params)
        if response.status_code == 200:
            try:
                return BlueskyData.model_validate(response.json())
            except ValidationError as e:
                await logger.aexception("[Medias/BlueSky] Validation failed: %s", e)
                return None
        return None


def get_caption(bluesky_data: BlueskyData) -> str:
    post = bluesky_data.thread.post
    display_name = post.author.display_name or "Unknown"
    handle = post.author.handle
    text = post.record.text

    caption = f"<b>{html.escape(display_name)} (<code>@{handle}</code>)</b>"
    if text:
        caption += f":\n\n{html.escape(text)}"

    return caption


async def process_media(
    bluesky_data: BlueskyData,
) -> list[MediaGroupItem] | None:
    embed = bluesky_data.thread.post.embed

    if embed and embed.embed_type:
        if "image" in embed.embed_type and embed.images:
            return await handle_image(embed.images)
        if "video" in embed.embed_type and embed.playlist and embed.thumbnail:
            return await handle_video(embed.playlist, embed.thumbnail)

    return None


async def handle_image(images: list[Image]) -> list[MediaGroupItem]:
    results: list[BytesIO | None] = [None] * len(images)

    async def fetch_image(index: int, image: Image) -> None:
        results[index] = await download_media(str(image.fullsize))

    async with create_task_group() as tg:
        for index, image in enumerate(images):
            tg.start_soon(fetch_image, index, image)

    media_items: list[MediaGroupItem] = [
        InputMediaPhoto(media=result) for result in results if result
    ]
    return media_items


async def handle_video(playlist_url: str, thumbnail_url: HttpUrl) -> list[MediaGroupItem] | None:
    async with httpx.AsyncClient(http2=True, timeout=20) as client:
        response = await client.get(playlist_url)
        if response.status_code != 200:
            return None

        playlist = m3u8.loads(response.text)
        highest_variant = max(
            playlist.playlists,
            key=lambda p: p.stream_info.bandwidth if p.stream_info.bandwidth is not None else 0,
        )
        video_url = urljoin(playlist_url, highest_variant.uri)
        resolution = highest_variant.stream_info.resolution

        if resolution:
            width, height = resolution
        else:
            width, height = 0, 0

        video = await download_media(video_url)
        if not video:
            return None

        thumbnail = await download_media(str(thumbnail_url))
        resized_thumbnail = thumbnail
        if thumbnail:
            await run_blocking(resize_thumbnail, thumbnail)

        return [
            InputMediaVideo(
                media=video,
                thumb=resized_thumbnail,
                width=width,
                height=height,
                supports_streaming=True,
            )
        ]

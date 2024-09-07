# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio
import re
from datetime import timedelta

import httpx
from cashews import NOT_NONE
from hydrogram.types import InputMediaPhoto
from pydantic import ValidationError

from korone.modules.medias.utils.cache import MediaCache
from korone.modules.medias.utils.files import url_to_bytes_io
from korone.utils.caching import cache
from korone.utils.logging import logger

from .types import BlueskyData


async def fetch_bluesky(text: str):
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
    match = re.search(r"([^/?#]+)/post/([A-Za-z0-9_-]+)", url)
    if match:
        return match.group(1), match.group(2)
    return None, None


@cache(ttl=timedelta(weeks=1), condition=NOT_NONE)
async def get_bluesky_data(username: str | None, post_id: str) -> BlueskyData | None:
    url = "https://public.api.bsky.app/xrpc/app.bsky.feed.getPostThread"
    params = {"uri": f"at://{username}/app.bsky.feed.post/{post_id}", "depth": "10"}
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
                await logger.aexception("[Medias/BlueSky] Error validating response: %s", e)
                return None
        return None


def get_caption(bluesky_data: BlueskyData) -> str:
    post = bluesky_data.thread.post
    display_name = post.author.display_name or "Unknown"
    text = post.record.text or ""
    return f"<b>{display_name} (<code>{post.author.handle}</code>)</b>:\n{text}"


async def process_media(bluesky_data: BlueskyData) -> list[InputMediaPhoto] | None:
    images = bluesky_data.thread.post.embed.images if bluesky_data.thread.post.embed else []
    if images is None:
        return None

    tasks = [url_to_bytes_io(image.fullsize, video=False) for image in images]

    results = await asyncio.gather(*tasks)

    return [InputMediaPhoto(media=result) for result in results if result]

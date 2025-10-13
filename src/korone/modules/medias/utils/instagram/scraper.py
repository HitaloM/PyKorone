# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M.

from __future__ import annotations

import re
from datetime import timedelta
from typing import TYPE_CHECKING

import httpx
from cashews import NOT_NONE
from hydrogram.types import InputMediaPhoto, InputMediaVideo
from lxml import html

from korone.modules.medias.utils.cache import MediaCache
from korone.modules.medias.utils.common import MediaGroupItem, ensure_url_scheme
from korone.modules.medias.utils.downloader import download_media
from korone.utils.caching import cache
from korone.utils.logging import get_logger

from .types import InstaFixData

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = get_logger(__name__)

POST_PATTERN = re.compile(r"(?:reel(?:s?)|p)/(?P<post_id>[A-Za-z0-9_-]+)")
INSTAGRAM_HOST = "instagram.com"
INSTAFIX_HOST = "eeinstagram.com"
TIMEOUT = 60
MAX_REDIRECTS = 5


async def fetch_instagram(post_url: str) -> Sequence[MediaGroupItem] | None:
    post_url = ensure_url_scheme(post_url)
    match = POST_PATTERN.search(post_url, re.IGNORECASE)
    if not match:
        return None

    post_id = match.group(1)
    insta = await get_instafix_data(post_url)
    if not insta or not insta.media_url:
        return None

    cache = MediaCache(post_id)
    media_list = await cache.get() or []

    if not media_list:
        media_list = await create_media_list(insta)

    if insta.description:
        media_list[-1].caption = format_caption(insta.username, insta.description)

    return media_list


async def create_media_list(insta: InstaFixData) -> list[MediaGroupItem]:
    media_list: list[MediaGroupItem] = []
    if insta.media_type == "photo":
        media = await download_media(str(insta.media_url))
        media_list.append(InputMediaPhoto(media=media))  # pyright: ignore[reportArgumentType]
    elif insta.media_type == "video":
        media = await download_media(str(insta.media_url))
        media_list.append(InputMediaVideo(media=media))  # pyright: ignore[reportArgumentType]
    return media_list


def format_caption(username: str | None, description: str | None) -> str:
    if not username and not description:
        return ""

    if username and description:
        return f"<b>{username}:</b>\n{description}"

    return f"<b>{username}<b>" if username else description or ""


@cache(ttl=timedelta(weeks=1), condition=NOT_NONE)
async def get_instafix_data(post_url: str) -> InstaFixData | None:
    normalized_url = ensure_url_scheme(post_url)
    if INSTAFIX_HOST in normalized_url:
        new_url = normalized_url
    else:
        new_url = normalized_url.replace(INSTAGRAM_HOST, INSTAFIX_HOST)

    new_url = ensure_url_scheme(new_url)

    async with httpx.AsyncClient(
        http2=True, timeout=TIMEOUT, max_redirects=MAX_REDIRECTS
    ) as client:
        try:
            response = await client.get(new_url, follow_redirects=True)
            if response.status_code != 200:
                return None

            real_url = response.url
            if not real_url:
                return None

            response = await client.get(real_url)
            response.raise_for_status()

            scraped_data = scrape_instafix_data(response.text)
            if not scraped_data["media_url"]:
                return None

            media_url = ensure_url_scheme(scraped_data["media_url"])
            video_response = await client.get(media_url, follow_redirects=True)
            scraped_data["media_url"] = str(video_response.url)

            return InstaFixData.model_validate(scraped_data)

        except (httpx.HTTPStatusError, httpx.RequestError) as e:
            await logger.aerror(
                "[Medias/Instagram] Fetch failed: %s, %s",
                post_url,
                str(e),
            )
            return None


def scrape_instafix_data(html_content: str) -> dict:
    tree = html.fromstring(html_content)
    meta_nodes = tree.xpath("//head/meta[@property or @name]")

    scraped_data = {"media_url": "", "username": "", "description": "", "type": ""}

    for node in meta_nodes:
        prop = node.get("property") or node.get("name")
        content = node.get("content")
        if prop == "og:video":
            scraped_data["type"] = "video"
            scraped_data["media_url"] = f"https://{INSTAFIX_HOST}{content}"
        elif prop == "twitter:title":
            scraped_data["username"] = content.lstrip("@")
        elif prop == "og:description":
            scraped_data["description"] = content
        elif prop == "og:image" and not scraped_data["media_url"]:
            scraped_data["type"] = "photo"
            content = content.replace(r"/images/", "/grid/")
            content = re.sub(r"/\d+$", "/", content)
            scraped_data["media_url"] = f"https://{INSTAFIX_HOST}{content}"

    return scraped_data

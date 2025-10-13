# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from __future__ import annotations

import html
import random
import re
import string
from datetime import timedelta
from typing import TYPE_CHECKING

import httpx
import orjson
from anyio import create_task_group
from cashews import NOT_NONE
from hydrogram.types import InputMediaPhoto, InputMediaVideo
from pydantic import ValidationError

from korone.modules.medias.utils.cache import MediaCache
from korone.modules.medias.utils.common import MediaGroupItem, ensure_url_scheme
from korone.modules.medias.utils.downloader import download_media
from korone.modules.medias.utils.files import resize_thumbnail
from korone.modules.medias.utils.generic_headers import GENERIC_HEADER
from korone.modules.medias.utils.instagram.scraper import fetch_instagram
from korone.utils.caching import cache
from korone.utils.concurrency import run_blocking
from korone.utils.logging import get_logger

from .types import CarouselMedia, Post, ThreadsData

if TYPE_CHECKING:
    from collections.abc import Sequence
    from io import BytesIO

logger = get_logger(__name__)


async def fetch_threads(text: str) -> Sequence[MediaGroupItem] | None:
    url = ensure_url_scheme(text)
    shortcode = get_shortcode(url)
    if not shortcode:
        return None

    post_id = await get_post_id(url)
    graphql_data = await get_gql_data(post_id)
    if not graphql_data or not graphql_data.data.data.edges:
        return None

    threads_post = graphql_data.data.data.edges[0].node.thread_items[0].post

    media_sequence: Sequence[MediaGroupItem] | None = None
    if threads_post.carousel_media:
        media_sequence = await handle_carousel(threads_post)
    elif threads_post.video_versions:
        media_sequence = await handle_video(threads_post)
    elif threads_post.image_versions2 and threads_post.image_versions2.candidates:
        media_sequence = await handle_image(threads_post)

    if not media_sequence:
        return None

    media_list = list(media_sequence)

    if (
        threads_post.text_post_app_info
        and threads_post.text_post_app_info.link_preview_attachment
        and threads_post.text_post_app_info.link_preview_attachment.display_url.startswith(
            "instagram.com"
        )
    ):
        return await fetch_instagram(threads_post.text_post_app_info.link_preview_attachment.url)

    caption = get_caption(graphql_data)

    cache = MediaCache(post_id)
    if cached_data := await cache.get():
        cached_data[-1].caption = caption
        return cached_data

    media_list[-1].caption = caption

    return media_list


def get_shortcode(url: str) -> str | None:
    match = re.search(r"(?:post)/([A-Za-z0-9_-]+)", url)
    return match[1] if match else None


@cache(ttl=timedelta(weeks=1), condition=NOT_NONE)
async def get_post_id(url: str) -> str:
    headers = GENERIC_HEADER.copy()
    headers.update({
        "Sec-Fetch-Mode": "navigate",
    })

    async with httpx.AsyncClient(http2=True, timeout=20) as client:
        response = await client.get(ensure_url_scheme(url), headers=headers)
        body = response.text

    id_location = body.find("post_id")
    if id_location == -1:
        return ""

    start = id_location + 10
    end = body.find('"', start)
    return "" if end == -1 else body[start:end]


def random_string(n: int) -> str:
    letters = string.ascii_letters + string.digits
    return "".join(random.choice(letters) for _ in range(n))


@cache(ttl=timedelta(weeks=1), condition=NOT_NONE)
async def get_gql_data(post_id: str) -> ThreadsData | None:
    url = "https://www.threads.com/api/graphql"
    lsd = random_string(10)
    headers = GENERIC_HEADER.copy()
    headers.update({
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Fb-Lsd": lsd,
        "X-Ig-App-Id": "238260118697367",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    })
    body = {
        "variables": orjson.dumps({
            "first": 1,
            "postID": post_id,
            "__relay_internal__pv__BarcelonaIsLoggedInrelayprovider": False,
            "__relay_internal__pv__BarcelonaIsThreadContextHeaderEnabledrelayprovider": False,
            "__relay_internal__pv__BarcelonaIsThreadContextHeaderFollowButtonEnabledrelayprovider": False,  # noqa: E501
            "__relay_internal__pv__BarcelonaUseCometVideoPlaybackEnginerelayprovider": False,
            "__relay_internal__pv__BarcelonaOptionalCookiesEnabledrelayprovider": False,
            "__relay_internal__pv__BarcelonaIsViewCountEnabledrelayprovider": False,
            "__relay_internal__pv__BarcelonaShouldShowFediverseM075Featuresrelayprovider": False,
        }).decode(),
        "doc_id": "7448594591874178",
        "lsd": lsd,
    }
    async with httpx.AsyncClient(http2=True, timeout=20) as client:
        response = await client.post(url, headers=headers, data=body)
        if response.status_code == 200:
            try:
                return ThreadsData.model_validate(response.json())
            except ValidationError as e:
                await logger.aerror("[Medias/Threads] GraphQL parse failed: %s", e)
                return None
        return None


def get_caption(threads_data: ThreadsData) -> str:
    post = threads_data.data.data.edges[0].node.thread_items[0].post
    username = post.user.username
    text = post.caption.text if post.caption else None

    caption = f"<b>{username}</b>"
    if text:
        caption += f":\n{html.escape(text)}"

    return caption


async def _process_carousel_media(media: CarouselMedia) -> MediaGroupItem | None:
    if media.video_versions:
        media_file = await download_media(media.video_versions[0].url)
        if not media_file:
            await logger.aerror("[Medias/Threads] Video download failed")
            return None

        thumbnail = None
        if media.image_versions2 and media.image_versions2.candidates:
            thumbnail_url = media.image_versions2.candidates[0].url
            thumbnail = await download_media(thumbnail_url)
            if thumbnail:
                await run_blocking(resize_thumbnail, thumbnail)

        return InputMediaVideo(
            media=media_file,
            width=media.original_width,
            height=media.original_height,
            supports_streaming=True,
            thumb=thumbnail,
        )

    if media.image_versions2 and media.image_versions2.candidates:
        media_file = await download_media(media.image_versions2.candidates[0].url)
        if not media_file:
            await logger.aerror("[Medias/Threads] Image download failed")
            return None

        return InputMediaPhoto(media=media_file)

    return None


async def handle_carousel(post: Post) -> list[MediaGroupItem]:
    if not post.carousel_media:
        return []

    media_list: list[MediaGroupItem] = []
    for media in post.carousel_media:
        processed = await _process_carousel_media(media)
        if processed:
            media_list.append(processed)

    return media_list


async def handle_video(post: Post) -> list[InputMediaVideo] | None:
    if not post.video_versions:
        return None

    video: BytesIO | None = None
    thumbnail: BytesIO | None = None

    async def fetch_video(url: str) -> None:
        nonlocal video
        video = await download_media(url)

    async def fetch_thumbnail(url: str) -> None:
        nonlocal thumbnail
        thumbnail = await download_media(url)

    video_url = post.video_versions[0].url
    thumb_url = None
    if post.image_versions2 and post.image_versions2.candidates:
        thumb_url = post.image_versions2.candidates[0].url

    async with create_task_group() as tg:
        tg.start_soon(fetch_video, video_url)
        if thumb_url:
            tg.start_soon(fetch_thumbnail, thumb_url)

    if not video:
        await logger.aerror("[Medias/Threads] Video download failed")
        return None

    if thumbnail:
        await run_blocking(resize_thumbnail, thumbnail)

    if post.original_width is None or post.original_height is None:
        return None

    return [
        InputMediaVideo(
            media=video,
            width=post.original_width,
            height=post.original_height,
            supports_streaming=True,
            thumb=thumbnail,
        )
    ]


async def handle_image(post: Post) -> list[InputMediaPhoto] | None:
    if not post.image_versions2 or not post.image_versions2.candidates:
        return None

    file = await download_media(post.image_versions2.candidates[0].url)
    if not file:
        await logger.aerror("[Medias/Threads] Image download failed")
        return None

    return [InputMediaPhoto(media=file)]

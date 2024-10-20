# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio
import html
import json
import random
import re
import string
from collections.abc import Sequence
from datetime import timedelta

import httpx
from cashews import NOT_NONE
from hydrogram.types import InputMedia, InputMediaPhoto, InputMediaVideo
from pydantic import ValidationError

from korone.modules.medias.utils.cache import MediaCache
from korone.modules.medias.utils.downloader import download_media
from korone.modules.medias.utils.files import resize_thumbnail
from korone.modules.medias.utils.instagram.scraper import fetch_instagram
from korone.utils.caching import cache
from korone.utils.logging import logger

from .types import Post, ThreadsData


async def fetch_threads(text: str) -> Sequence[InputMedia] | None:
    shortcode = get_shortcode(text)
    if not shortcode:
        return None

    post_id = await get_post_id(text)
    graphql_data = await get_gql_data(post_id)
    if not graphql_data or not graphql_data.data.data.edges:
        return None

    threads_post = graphql_data.data.data.edges[0].node.thread_items[0].post

    media_list = []
    if threads_post.carousel_media:
        media_list = await handle_carousel(threads_post)
    elif threads_post.video_versions:
        media_list = await handle_video(threads_post)
    elif threads_post.image_versions2 and threads_post.image_versions2.candidates:
        media_list = await handle_image(threads_post)

    if not media_list:
        return None

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
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "Sec-Fetch-Mode": "navigate",
    }

    async with httpx.AsyncClient(http2=True, timeout=20) as client:
        response = await client.get(url, headers=headers)
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
    url = "https://www.threads.net/api/graphql"
    lsd = random_string(10)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36 Edg/128.0.0.0",
        "Content-Type": "application/x-www-form-urlencoded",
        "X-Fb-Lsd": lsd,
        "X-Ig-App-Id": "238260118697367",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-origin",
    }
    body = {
        "variables": json.dumps({
            "first": 1,
            "postID": post_id,
            "__relay_internal__pv__BarcelonaIsLoggedInrelayprovider": False,
            "__relay_internal__pv__BarcelonaIsThreadContextHeaderEnabledrelayprovider": False,
            "__relay_internal__pv__BarcelonaIsThreadContextHeaderFollowButtonEnabledrelayprovider": False,  # noqa: E501
            "__relay_internal__pv__BarcelonaUseCometVideoPlaybackEnginerelayprovider": False,
            "__relay_internal__pv__BarcelonaOptionalCookiesEnabledrelayprovider": False,
            "__relay_internal__pv__BarcelonaIsViewCountEnabledrelayprovider": False,
            "__relay_internal__pv__BarcelonaShouldShowFediverseM075Featuresrelayprovider": False,
        }),
        "doc_id": "7448594591874178",
        "lsd": lsd,
    }
    async with httpx.AsyncClient(http2=True, timeout=20) as client:
        response = await client.post(url, headers=headers, data=body)
        if response.status_code == 200:
            try:
                return ThreadsData.model_validate(response.json())
            except ValidationError as e:
                await logger.aerror("[Medias/Threads] Error parsing GraphQL data: %s", e)
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


async def handle_carousel(post: Post) -> list[InputMedia]:
    tasks = []
    if post.carousel_media:
        for media in post.carousel_media:
            if media.video_versions:
                if media.image_versions2 and media.image_versions2.candidates:
                    tasks.append(download_media(media.video_versions[0].url))
            elif media.image_versions2 and media.image_versions2.candidates:
                tasks.append(download_media(media.image_versions2.candidates[0].url))
    media_files = await asyncio.gather(*tasks)
    media_list = []
    if media_files is not None and post.carousel_media is not None:
        for media, media_file in zip(post.carousel_media, media_files, strict=False):
            if media.video_versions:
                media_list.append(
                    InputMediaVideo(
                        media=media_file,
                        width=media.original_width,
                        height=media.original_height,
                        supports_streaming=True,
                        thumb=media.image_versions2.candidates[0].url
                        if media.image_versions2 and media.image_versions2.candidates
                        else None,
                    )
                )
            else:
                media_list.append(InputMediaPhoto(media=media_file))
    return media_list


async def handle_video(post: Post) -> list[InputMediaVideo] | None:
    if not post.video_versions:
        return None

    file = await download_media(post.video_versions[0].url)
    if not file:
        return None

    thumbnail = (
        await download_media(post.image_versions2.candidates[0].url)
        if post.image_versions2 and post.image_versions2.candidates
        else None
    )
    if thumbnail:
        resized_thumbnail = await asyncio.to_thread(resize_thumbnail, thumbnail)

    if post.original_width is None or post.original_height is None:
        return None

    return [
        InputMediaVideo(
            media=file,
            width=post.original_width,
            height=post.original_height,
            supports_streaming=True,
            thumb=resized_thumbnail,
        )
    ]


async def handle_image(post: Post) -> list[InputMediaPhoto] | None:
    if post.image_versions2 and post.image_versions2.candidates:
        file = await download_media(post.image_versions2.candidates[0].url)
        if not file:
            return None

    return None if not file else [InputMediaPhoto(media=file)]

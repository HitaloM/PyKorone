# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio
import re
from collections.abc import Mapping, Sequence
from datetime import timedelta
from typing import Any

import httpx
from cashews import NOT_NONE
from hydrogram.types import InputMedia, InputMediaPhoto, InputMediaVideo
from lxml import html

from korone import cache
from korone.modules.medias.utils.cache import MediaCache
from korone.utils.logging import logger

from .downloader import download_media
from .types import InstaFixData, InstagramData, Node, ShortcodeMedia

POST_PATTERN = re.compile(r"(?:reel(?:s?)|p)/(?P<post_id>[A-Za-z0-9_-]+)")


NodeDict = Mapping[str, str]
EdgeDict = Mapping[str, NodeDict]
EdgeMediaToCaptionDict = Mapping[str, list[EdgeDict]]
OwnerDict = Mapping[str, str]
ShortcodeMediaDict = Mapping[str, str | Any | EdgeMediaToCaptionDict | OwnerDict | None]
MediaDataDict = Mapping[str, ShortcodeMediaDict]


async def fetch_with_retries(
    url: str, headers: dict, max_retries: int = 3, retry_delay: int = 2
) -> str | None:
    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(http2=True, timeout=20) as client:
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.text
        except httpx.ConnectError as e:
            await logger.aerror(
                "[Medias/Instagram] Connection attempt %s failed: %s", attempt + 1, e
            )
            if attempt < max_retries - 1:
                await asyncio.sleep(retry_delay)
            else:
                raise
        except httpx.HTTPStatusError as e:
            await logger.aerror("[Medias/Instagram] HTTP error occurred: %s", e)
            raise
    return None


def extract_gql_data(response_text: str) -> str | None:
    match = re.search(r"\\\"gql_data\\\":([\s\S]*?)\}\"", response_text)
    if match:
        gql_data = match.group(1)
        return gql_data.replace(r"\"", '"').replace(r"\\/", "/").replace(r"\\", "\\")
    return None


async def extract_media_data(response_text: str, post_id: str) -> dict[str, Any] | None:
    def clean_html(raw_html: str) -> str:
        return re.sub(r"<[^>]*>", "", raw_html).strip()

    media_type_match = re.search(r'data-media-type="(.*?)"', response_text)
    main_media_match = re.search(r'class="Content.*?src="(.*?)"', response_text)
    caption_match = re.search(
        r'class="Caption".*?'
        r'class="CaptionUsername".*?'
        r'data-log-event="captionProfileClick" target="_blank">'
        r"(.*?)<\/a>(.*?)<div",
        response_text,
        re.DOTALL,
    )
    username_match = re.search(r'class="UsernameText">([^<]+)</span>', response_text, re.DOTALL)

    if not media_type_match or not main_media_match:
        return None

    media_type = media_type_match.group(1)
    main_media_url = main_media_match.group(1).replace("amp;", "")
    owner = (
        clean_html(username_match.group(1))
        if username_match
        else clean_html(caption_match.group(1))
        if caption_match
        else None
    )
    caption = clean_html(caption_match.group(2)) if caption_match else None

    if media_type == "GraphVideo":
        instafix_data = await get_instafix_data(post_id)
        if not instafix_data:
            return None
        return {
            "shortcode_media": {
                "__typename": media_type,
                "display_url": main_media_url,
                "video_url": instafix_data.video_url,
                "edge_media_to_caption": {"edges": [{"node": {"text": caption}}]},
                "owner": {"username": owner},
            }
        }

    return {
        "shortcode_media": {
            "__typename": media_type,
            "display_url": main_media_url,
            "edge_media_to_caption": {"edges": [{"node": {"text": caption}}]},
            "owner": {"username": owner},
        }
    }


@cache(ttl=timedelta(weeks=1), condition=NOT_NONE)
async def get_embed_data(url: str) -> InstagramData | None:
    match = POST_PATTERN.search(url)
    if not match:
        return None

    post_id = match.group(1)
    embed_url = f"https://www.instagram.com/p/{post_id}/embed/captioned/"
    headers = {
        "accept": (
            "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,"
            "image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9"
        ),
        "accept-language": "en-US,en;q=0.9",
        "connection": "close",
        "sec-fetch-mode": "navigate",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
        "viewport-width": "1280",
    }

    try:
        response_data = await fetch_with_retries(embed_url, headers)
    except (httpx.ConnectError, httpx.HTTPStatusError):
        return None

    if not response_data:
        return None

    gql_data = extract_gql_data(response_data)
    if gql_data and gql_data != "null":
        return InstagramData.model_validate_json(gql_data)

    instafix_data = await get_instafix_data(url)
    if instafix_data:
        instafix_dict = {
            "shortcode_media": {
                "__typename": "GraphVideo",
                "video_url": instafix_data.video_url,
                "edge_media_to_caption": {
                    "edges": [{"node": {"text": instafix_data.description}}]
                },
                "owner": {"username": instafix_data.username},
            }
        }
        return InstagramData.model_validate(instafix_dict)

    media_data = await extract_media_data(response_data, post_id)
    if media_data:
        return InstagramData.model_validate(media_data)

    return None


@cache(ttl=timedelta(weeks=1), condition=NOT_NONE)
async def get_instafix_data(post_url: str) -> InstaFixData | None:
    host = "ddinstagram.com"
    new_url = post_url.replace("instagram.com", host)

    async with httpx.AsyncClient(
        http2=True, timeout=20, headers={"User-Agent": "curl"}, max_redirects=1
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

            tree = html.fromstring(response.text)
            meta_nodes = tree.xpath("//head/meta[@property or @name]")

            scraped_data = {"video_url": "", "username": "", "description": ""}

            for node in meta_nodes:
                prop = node.get("property") or node.get("name")
                content = node.get("content")
                if prop == "og:video":
                    scraped_data["video_url"] = f"https://{host}{content}"
                elif prop == "twitter:title":
                    scraped_data["username"] = content.lstrip("@")
                elif prop == "og:description":
                    scraped_data["description"] = content
                elif prop == "og:image" and not scraped_data["video_url"]:
                    scraped_data["video_url"] = f"https://{host}{content}"

            if not scraped_data["video_url"]:
                return None

            video_response = await client.get(scraped_data["video_url"], follow_redirects=True)
            scraped_data["video_url"] = str(video_response.url)

            return InstaFixData.model_validate(scraped_data)

        except (httpx.HTTPStatusError, httpx.RequestError):
            return None


async def instagram(url: str) -> Sequence[InputMedia] | None:
    match = POST_PATTERN.search(url)
    if not match:
        return None

    post_id = match.group(1)
    instagram_data = await get_embed_data(url)
    if not instagram_data and (
        not instagram_data
        or not instagram_data.data
        or not instagram_data.data.xdt_shortcode_media
    ):
        return None

    shortcode_media = instagram_data.data.xdt_shortcode_media if instagram_data.data else None
    if not shortcode_media:
        shortcode_media = instagram_data.shortcode_media
    if not shortcode_media:
        return None

    caption = extract_caption(shortcode_media)

    cache = MediaCache(post_id)
    cached_media = await cache.get()

    if cached_media:
        media_items = extract_media_items_from_cache(cached_media)
    else:
        media_items = await extract_media_items(shortcode_media)

    if media_items:
        media_items[-1].caption = caption

    return media_items


def extract_media_items_from_cache(cached_data: dict) -> Sequence[InputMedia]:
    def create_photo(media):
        return InputMediaPhoto(media=media["file"])

    def create_video(media):
        return InputMediaVideo(
            media=media["file"],
            duration=media["duration"],
            width=media["width"],
            height=media["height"],
            thumb=media["thumbnail"],
        )

    photos = [create_photo(media) for media in cached_data.get("photo", [])]
    videos = [create_video(media) for media in cached_data.get("video", [])]

    return photos + videos


def extract_caption(shortcode_media: ShortcodeMedia) -> str:
    caption_builder: list[str] = []

    owner_username = getattr(shortcode_media.owner, "username", None)
    if owner_username:
        caption_builder.append(f"<b>{owner_username}:</b>")

    if shortcode_media.coauthor_producers:
        caption_builder.extend(
            f"<b>{coauthor.username}:</b>"
            for coauthor in shortcode_media.coauthor_producers
            if coauthor and coauthor.username
        )

    caption_edges = getattr(shortcode_media.edge_media_to_caption, "edges", [])
    if caption_edges:
        caption_text = getattr(caption_edges[0].node, "text", "")
        if caption_text:
            caption_builder.append(caption_text[:255])

    return "\n".join(caption_builder)


async def extract_media_items(shortcode_media) -> list[InputMedia] | None:
    media_items: list[InputMedia] = []

    async def process_media_item(process_func, media_url):
        if media_url:
            item = await process_func(shortcode_media)
            if item:
                media_items.append(item)

    typename = shortcode_media.typename
    if typename in {"GraphVideo", "XDTGraphVideo"}:
        await process_media_item(process_video_item, shortcode_media.video_url)
    elif typename in {"GraphImage", "XDTGraphImage"}:
        await process_media_item(process_image_item, shortcode_media.display_url)
    elif typename in {"GraphSidecar", "XDTGraphSidecar"} and (
        shortcode_media.edge_sidecar_to_children and shortcode_media.edge_sidecar_to_children.edges
    ):
        media_download_tasks = [
            process_sidecar_node(edge.node)
            for edge in shortcode_media.edge_sidecar_to_children.edges
            if edge.node
        ]
        sidecar_medias = await asyncio.gather(*media_download_tasks)
        media_items.extend(item for item in sidecar_medias if item is not None)

    return media_items or None


async def process_video_item(shortcode_media: ShortcodeMedia) -> InputMedia | None:
    video_file = (
        await download_media(str(shortcode_media.video_url)) if shortcode_media.video_url else None
    )

    thumbnail = (
        await download_media(shortcode_media.display_resources[-1].src)
        if shortcode_media.display_resources and shortcode_media.display_resources[-1].src
        else None
    )

    if video_file:
        width = (
            shortcode_media.dimensions.width
            if shortcode_media.dimensions and shortcode_media.dimensions.width is not None
            else 0
        )
        height = (
            shortcode_media.dimensions.height
            if shortcode_media.dimensions and shortcode_media.dimensions.height is not None
            else 0
        )
        return InputMediaVideo(
            media=video_file,
            thumb=thumbnail,
            width=width,
            height=height,
            supports_streaming=True,
        )
    return None


async def process_image_item(shortcode_media: ShortcodeMedia) -> InputMedia | None:
    file = await download_media(str(shortcode_media.display_url))
    return InputMediaPhoto(media=file) if file else None


async def process_sidecar_node(node: Node) -> InputMedia | None:
    async def download_thumbnail(resources):
        if resources:
            return await download_media(resources[-1]["src"])
        return None

    if node.is_video and node.video_url:
        video_file = await download_media(str(node.video_url))
        if video_file:
            thumbnail = await download_thumbnail(node.display_resources)
            return InputMediaVideo(
                media=video_file,
                thumb=thumbnail,
                width=node.dimensions.get("width", 0) if node.dimensions else 0,
                height=node.dimensions.get("height", 0) if node.dimensions else 0,
                supports_streaming=True,
            )

    if node.display_resources:
        image_file = await download_media(node.display_resources[-1]["src"])
        if image_file:
            return InputMediaPhoto(image_file)

    return None

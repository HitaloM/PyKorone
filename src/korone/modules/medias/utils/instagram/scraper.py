# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio
import contextlib
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

from .downloader import download_media
from .types import InstaFixData, InstagramData, Node, ShortcodeMedia

POST_PATTERN = re.compile(r"(?:reel(?:s?)|p)/(?P<post_id>[A-Za-z0-9_-]+)")


NodeDict = Mapping[str, str]
EdgeDict = Mapping[str, NodeDict]
EdgeMediaToCaptionDict = Mapping[str, list[EdgeDict]]
OwnerDict = Mapping[str, str]
ShortcodeMediaDict = Mapping[str, str | Any | EdgeMediaToCaptionDict | OwnerDict | None]
MediaDataDict = Mapping[str, ShortcodeMediaDict]


def extract_gql_data(response_text: str) -> str | None:
    match = re.search(r"\\\"gql_data\\\":([\s\S]*)\}\"\}", response_text)
    if match:
        return match.group(1).replace(r"\"", '"').replace(r"\\/", "/").replace(r"\\", "\\")
    return None


async def extract_media_data(response_text: str, post_id: str) -> MediaDataDict | None:
    media_type = re.search(r'data-media-type="(.*?)"', response_text)
    if not media_type:
        return None

    media_type = media_type.group(1)
    main_media = re.search(r'class="Content.*?src="(.*?)"', response_text)
    if not main_media:
        return None

    main_media_url = main_media.group(1).replace("amp;", "")
    caption_data = re.search(
        r'class="Caption".*?'
        r'class="CaptionUsername".*?'
        r'data-log-event="captionProfileClick" target="_blank">'
        r"(.*?)<\/a>(.*?)<div",
        response_text,
        re.DOTALL,
    )

    username_data = re.search(
        r'class="UsernameText">([^<]+)</span>',
        response_text,
        re.DOTALL,
    )

    if not caption_data and not username_data:
        return None

    owner: str | None = None
    caption: str | None = None

    if username_data:
        owner = re.sub(r"<[^>]*>", "", username_data.group(1)).strip()
    elif caption_data:
        owner = re.sub(r"<[^>]*>", "", caption_data.group(1)).strip()

    if caption_data:
        caption = re.sub(r"<[^>]*>", "", caption_data.group(2)).strip()

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
    async with httpx.AsyncClient(http2=True, timeout=20) as client:
        try:
            response = await client.get(
                embed_url,
                headers={
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
                },
            )
            response.raise_for_status()
        except httpx.HTTPStatusError:
            return None

    gql_data = extract_gql_data(response.text)
    result: InstagramData | None = None

    if gql_data and gql_data != "null":
        with contextlib.suppress(ValueError):
            result = InstagramData.model_validate_json(gql_data)
    else:
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
            result = InstagramData.model_validate(instafix_dict)

    if not result:
        media_data = await extract_media_data(response.text, post_id)
        if media_data:
            result = InstagramData.model_validate(media_data)

    return result


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

            scraped_data = {}
            for node in meta_nodes:
                prop = node.get("property") or node.get("name")
                content = node.get("content")
                if prop == "og:video":
                    scraped_data["video_url"] = f"https://{host}{content}"
                elif prop == "twitter:title":
                    scraped_data["username"] = content.lstrip("@")
                elif prop == "og:description":
                    scraped_data["description"] = content
                elif prop == "og:image" and "video_url" not in scraped_data:
                    scraped_data["video_url"] = f"https://{host}{content}"

            if "video_url" not in scraped_data:
                return None

            video_response = await client.get(scraped_data["video_url"], follow_redirects=True)
            scraped_data["video_url"] = str(video_response.url)

            return InstaFixData(**scraped_data)

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
        if media_items:
            media_items[-1].caption = caption
            return media_items

    media_items = await extract_media_items(shortcode_media)

    if media_items:
        media_items[-1].caption = caption

    return media_items


def extract_media_items_from_cache(cached_data: dict) -> Sequence[InputMedia]:
    photos = [InputMediaPhoto(media=media["file"]) for media in cached_data.get("photo", [])]
    videos = [
        InputMediaVideo(
            media=media["file"],
            duration=media["duration"],
            width=media["width"],
            height=media["height"],
            thumb=media["thumbnail"],
        )
        for media in cached_data.get("video", [])
    ]
    return photos + videos


def extract_caption(shortcode_media: ShortcodeMedia) -> str:
    caption_builder: list[str] = []
    if shortcode_media.owner and shortcode_media.owner.username:
        caption_builder.append(f"<b>{shortcode_media.owner.username}:</b>")

    if shortcode_media.coauthor_producers is not None:
        caption_builder.extend([
            f"<b>{coauthor.username}:</b>"
            for coauthor in shortcode_media.coauthor_producers
            if coauthor and coauthor.username
        ])

    if (
        shortcode_media.edge_media_to_caption
        and shortcode_media.edge_media_to_caption.edges
        and shortcode_media.edge_media_to_caption.edges[0].node
        and shortcode_media.edge_media_to_caption.edges[0].node.text
    ):
        caption_builder.append(
            shortcode_media.edge_media_to_caption.edges[0].node.text[:255]
            if len(shortcode_media.edge_media_to_caption.edges[0].node.text) > 255
            else shortcode_media.edge_media_to_caption.edges[0].node.text
        )
    return "\n".join(caption_builder)


async def extract_media_items(shortcode_media) -> list[InputMedia] | None:
    media_items: list[InputMedia] = []

    if shortcode_media.typename in {"GraphVideo", "XDTGraphVideo"}:
        if shortcode_media.video_url:
            video_item = await process_video_item(shortcode_media)
            if video_item:
                media_items.append(video_item)
    elif shortcode_media.typename in {"GraphImage", "XDTGraphImage"}:
        if shortcode_media.display_url:
            image_item = await process_image_item(shortcode_media)
            if image_item:
                media_items.append(image_item)
    elif shortcode_media.typename in {"GraphSidecar", "XDTGraphSidecar"} and (
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
    file = None
    if shortcode_media.video_url:
        file = await download_media(str(shortcode_media.video_url))
    thumbnail = None
    if shortcode_media.display_resources and shortcode_media.display_resources[-1].src:
        thumbnail = await download_media(shortcode_media.display_resources[-1].src)
    return (
        InputMediaVideo(
            media=file,
            thumb=thumbnail,
            width=shortcode_media.dimensions.width
            if shortcode_media.dimensions and shortcode_media.dimensions.width is not None
            else 0,
            height=shortcode_media.dimensions.height
            if shortcode_media.dimensions and shortcode_media.dimensions.height is not None
            else 0,
            supports_streaming=True,
        )
        if file
        else None
    )


async def process_image_item(shortcode_media: ShortcodeMedia) -> InputMedia | None:
    file = await download_media(str(shortcode_media.display_url))
    return InputMediaPhoto(media=file) if file else None


async def process_sidecar_node(node: Node) -> InputMedia | None:
    if node.is_video and node.video_url:
        file = await download_media(str(node.video_url))
        thumbnail = None
        if node.display_resources:
            thumbnail = await download_media(node.display_resources[-1]["src"])
        return (
            InputMediaVideo(
                media=file,
                thumb=thumbnail,
                width=node.dimensions["width"] if node.dimensions else 0,
                height=node.dimensions["height"] if node.dimensions else 0,
                supports_streaming=True,
            )
            if file
            else None
        )
    if node.display_resources:
        file = await download_media(node.display_resources[-1]["src"])
        return InputMediaPhoto(file) if file else None
    return None

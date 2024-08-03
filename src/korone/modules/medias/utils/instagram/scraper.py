# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio
import contextlib
import json
import re

import httpx
from hydrogram.types import InputMedia, InputMediaPhoto, InputMediaVideo
from lxml import html

from korone.modules.medias.utils.cache import MediaCache
from korone.modules.medias.utils.instagram.downloader import downloader
from korone.modules.medias.utils.instagram.types import (
    InstaFixData,
    InstagramData,
    Node,
    ShortcodeMedia,
)

POST_PATTERN = re.compile(r"(?:reel(?:s?)|p)/(?P<post_id>[A-Za-z0-9_-]+)")


def extract_gql_data(response_text: str) -> str | None:
    match = re.search(r"\\\"gql_data\\\":([\s\S]*)\}\"\}", response_text)
    if match:
        return match.group(1).replace(r"\"", '"').replace(r"\\/", "/").replace(r"\\", "\\")
    return None


async def extract_media_data(response_text: str, post_id: str) -> dict | None:
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

    owner = None
    caption = None

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


async def get_embed_data(post_id: str) -> InstagramData | None:
    url = f"https://www.instagram.com/p/{post_id}/embed/captioned/"
    async with httpx.AsyncClient(http2=True, timeout=20) as client:
        try:
            response = await client.get(
                url,
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
    result = None

    if gql_data and gql_data != "null":
        with contextlib.suppress(ValueError):
            result = InstagramData.model_validate_json(gql_data)
    else:
        instafix_data = await get_instafix_data(post_id)
        if instafix_data:
            instafix_dict = {
                "shortcode_media": {
                    "__typename": "GraphVideo",
                    "video_url": instafix_data.video_url,
                    "edge_media_to_caption": {
                        "edges": [{"node": {"text": instafix_data.author_name}}]
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


async def get_gql_data(post_id: str) -> InstagramData | None:
    url = "https://www.instagram.com/api/graphql"

    params = {
        "av": "0",
        "__d": "www",
        "__user": "0",
        "__a": "1",
        "__req": "3",
        "__hs": "19734.HYP:instagram_web_pkg.2.1..0.0",
        "dpr": "1",
        "__ccg": "UNKNOWN",
        "__rev": "1010782723",
        "__s": "qg5qgx:efei15:ng6310",
        "__hsi": "7323030086241513400",
        "__dyn": (
            "7xeUjG1mxu1syUbFp60DU98nwgU29zEdEc8co2qwJw5ux609vCwjE1xoswIwuo2awlU-cw5Mx62G3i1yw"
            "Owv89k2C1Fwc60AEC7U2czXwae4UaEW2G1NwwwNwKwHw8Xxm16wUxO1px-0iS2S3qazo7u1xwIwbS1LwT"
            "wKG1pg661pwr86C1mwrd6goK68jxe6V8"
        ),
        "__csr": (
            "gps8cIy8WTDAqjWDrpda9SoLHhaVeVEgvhaJzVQ8hF-qEPBV8O4EhGmciDBQh1mVuF9V9d2FHGicAVu8G"
            "AmfZiHzk9IxlhV94aKC5oOq6Uhx-Ku4Kaw04Jrx64-0oCdw0MXw1lm0EE2Ixcjg2Fg1JEko0N8U421tw6"
            "2wq8989EMw1QpV60CE02BIw"
        ),
        "__comet_req": "7",
        "lsd": "AVp2LurCmJw",
        "jazoest": "2989",
        "__spin_r": "1010782723",
        "__spin_b": "trunk",
        "__spin_t": "1705025808",
        "fb_api_caller_class": "RelayModern",
        "fb_api_req_friendly_name": "PolarisPostActionLoadPostQueryQuery",
        "query_hash": "b3055c01b4b222b8a47dc12b090e4e64",
        "variables": json.dumps({
            "shortcode": post_id,
            "fetch_comment_count": 2,
            "fetch_related_profile_media_count": 0,
            "parent_comment_count": 0,
            "child_comment_count": 0,
            "fetch_like_count": 10,
            "fetch_tagged_user_count": None,
            "fetch_preview_comment_count": 2,
            "has_threaded_comments": True,
            "hoisted_comment_id": None,
            "hoisted_reply_id": None,
        }),
        "server_timestamps": "true",
        "doc_id": "10015901848480474",
    }

    body = "&".join([f"{key}={value}" for key, value in params.items()]).encode()

    async with httpx.AsyncClient(http2=True, timeout=20) as client:
        response = await client.post(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:120.0) "
                "Gecko/20100101 Firefox/120.0",
                "Accept": "*/*",
                "Accept-Language": "en-US;q=0.5,en;q=0.3",
                "Content-Type": "application/x-www-form-urlencoded",
                "X-FB-Friendly-Name": "PolarisPostActionLoadPostQueryQuery",
                "X-CSRFToken": "-m5n6c-w1Z9RmrGqkoGTMq",
                "X-IG-App-ID": "936619743392459",
                "X-FB-LSD": "AVp2LurCmJw",
                "X-ASBD-ID": "129477",
                "DNT": "1",
                "Sec-Fetch-Dest": "empty",
                "Sec-Fetch-Mode": "cors",
                "Sec-Fetch-Site": "same-origin",
            },
            content=body,
        )

    if response.status_code != 200:
        return None

    try:
        return InstagramData.model_validate_json(response.text)
    except ValueError:
        return None


async def get_instafix_data(post_id: str) -> InstaFixData | None:
    video_url = f"https://ddinstagram.com/videos/{post_id}/1"
    oembed_url = f"https://www.ddinstagram.com/reels/{post_id}/"

    async with httpx.AsyncClient(http2=True, timeout=20, headers={"User-Agent": "bot"}) as client:
        try:
            video_response = await client.get(video_url)
            if video_response.status_code != 302:
                return None

            video_tree = html.fromstring(video_response.text)
            video_link = video_tree.xpath("//a[@href]/@href")
            if not video_link:
                return None
            video_link = video_link[0]

            oembed_response = await client.get(oembed_url)
            oembed_response.raise_for_status()

            oembed_tree = html.fromstring(oembed_response.text)
            oembed_link = oembed_tree.xpath('//link[@type="application/json+oembed"]/@href')
            if not oembed_link:
                return None
            oembed_link = f"https://{oembed_link[0]}"

            oembed_data_response = await client.get(oembed_link)
            oembed_data_response.raise_for_status()

            oembed_data = oembed_data_response.json()
            oembed_data["video_url"] = video_link

            username = oembed_tree.xpath('//link[@type="application/json+oembed"]/@title')
            if not username:
                return None

            oembed_data["username"] = username[0].lstrip("@")

            return InstaFixData(**oembed_data)
        except httpx.HTTPStatusError:
            return None


async def instagram(url: str) -> list[InputMediaVideo | InputMediaPhoto] | None:
    media_items = []
    caption: str = ""

    match = POST_PATTERN.search(url)
    if not match:
        return None

    post_id = match.group(1)

    instagram_data = await get_embed_data(post_id)
    if not instagram_data:
        instagram_data = await get_gql_data(post_id)
        if (
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


def extract_media_items_from_cache(cached_data: dict) -> list[InputMediaVideo | InputMediaPhoto]:
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
    caption_builder = []
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


async def extract_media_items(shortcode_media) -> list[InputMediaVideo | InputMediaPhoto]:
    media_items = []
    if shortcode_media.typename in {"GraphVideo", "XDTGraphVideo"}:
        if shortcode_media.video_url:
            media_items.append(await process_video_item(shortcode_media))
    elif shortcode_media.typename in {"GraphImage", "XDTGraphImage"}:
        if shortcode_media.display_url:
            media_items.append(await process_image_item(shortcode_media))
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
    return media_items


async def process_video_item(shortcode_media: ShortcodeMedia) -> InputMedia:
    file = None
    if shortcode_media.video_url:
        file = await downloader(str(shortcode_media.video_url))
    thumbnail = None
    if shortcode_media.display_resources and shortcode_media.display_resources[-1].src:
        thumbnail = await downloader(shortcode_media.display_resources[-1].src)
    return InputMediaVideo(
        media=file,  # type: ignore
        thumb=thumbnail,
        width=shortcode_media.dimensions.width
        if shortcode_media.dimensions and shortcode_media.dimensions.width is not None
        else 0,
        height=shortcode_media.dimensions.height
        if shortcode_media.dimensions and shortcode_media.dimensions.height is not None
        else 0,
        supports_streaming=True,
    )


async def process_image_item(shortcode_media: ShortcodeMedia) -> InputMedia | None:
    file = await downloader(str(shortcode_media.display_url))
    return InputMediaPhoto(media=file) if file else None


async def process_sidecar_node(node: Node) -> InputMedia | None:
    if node.is_video and node.video_url:
        file = await downloader(str(node.video_url))
        thumbnail = None
        if node.display_resources:
            thumbnail = await downloader(node.display_resources[-1]["src"])
        return InputMediaVideo(
            media=file,  # type: ignore
            thumb=thumbnail,
            width=node.dimensions["width"] if node.dimensions else 0,
            height=node.dimensions["height"] if node.dimensions else 0,
            supports_streaming=True,
        )
    if node.display_resources:
        file = await downloader(node.display_resources[-1]["src"])
        return InputMediaPhoto(file) if file else None
    return None

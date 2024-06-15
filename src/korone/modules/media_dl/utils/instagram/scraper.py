# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import re
from dataclasses import dataclass
from datetime import timedelta
from enum import Enum
from typing import Any

import esprima
import httpx
import orjson
from bs4 import BeautifulSoup, NavigableString, PageElement, Tag

from korone import cache
from korone.config import ConfigManager
from korone.utils.logging import log

TIMEOUT: int = 20
HEADERS: dict[str, str] = {
    "accept": "*/*",
    "accept-language": "en-US,en;q=0.9",
    "content-type": "application/x-www-form-urlencoded",
    "origin": "https://www.instagram.com",
    "priority": "u=1, i",
    "sec-ch-prefers-color-scheme": "dark",
    "sec-ch-ua": '"Google Chrome";v="125", "Chromium";v="125", "Not.A/Brand";v="24"',
    "sec-ch-ua-full-version-list": (
        '"Google Chrome";v="125.0.6422.142", '
        '"Chromium";v="125.0.6422.142", '
        '"Not.A/Brand";v="24.0.0.0"'
    ),
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-model": "",
    "sec-ch-ua-platform": '"macOS"',
    "sec-ch-ua-platform-version": '"12.7.4"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-origin",
    "user-agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    ),
    "x-asbd-id": "129477",
    "x-bloks-version-id": "e2004666934296f275a5c6b2c9477b63c80977c7cc0fd4b9867cb37e36092b68",
    "x-fb-friendly-name": "PolarisPostActionLoadPostQueryQuery",
    "x-ig-app-id": "936619743392459",
}


class MediaType(Enum):
    GRAPH_IMAGE = "GraphImage"
    GRAPH_VIDEO = "GraphVideo"
    STORY_IMAGE = "StoryImage"
    STORY_VIDEO = "StoryVideo"


class InstaError(Exception):
    pass


class NotFoundError(InstaError):
    pass


@dataclass
class Media:
    type_name: MediaType
    url: str


@dataclass
class InstaData:
    post_id: str
    username: str
    caption: str | None
    medias: list[Media]


def gq_text_new_line(s: Tag | PageElement | None) -> str:
    if s is None:
        return ""

    result = [
        c
        if isinstance(c, NavigableString)
        else "\n"
        if getattr(c, "name", "") == "br"
        else gq_text_new_line(c)
        for c in getattr(s, "children", [])
    ]

    return "".join(result)


def parse_embed_html(embed_html: str) -> bytes:
    doc = BeautifulSoup(embed_html, "lxml")
    typename, media_url = get_typename_and_media_url(doc)
    username = get_username(doc)
    caption = get_caption(doc)
    video_blocked = "WatchOnInstagram" in embed_html

    return construct_json_response(typename, media_url, username, caption, video_blocked)


def get_typename_and_media_url(
    doc: BeautifulSoup,
) -> tuple[MediaType, str | list[str] | None]:
    typename = MediaType.GRAPH_IMAGE
    embed_media = doc.select_one(".EmbeddedMediaImage")
    if embed_media is None:
        typename = MediaType.GRAPH_VIDEO
        embed_media = doc.select_one(".EmbeddedMediaVideo")
    media_url = embed_media.get("src") if embed_media else None
    return typename, media_url


def get_username(doc: BeautifulSoup) -> str | None:
    username_element = doc.select_one(".UsernameText")
    return username_element.get_text() if username_element else None


def get_caption(doc: BeautifulSoup) -> str | None:
    caption_comments = doc.select_one(".CaptionComments")
    if caption_comments:
        caption_comments.decompose()
    caption_username = doc.select_one(".CaptionUsername")
    if caption_username:
        caption_username.decompose()
    caption_element = doc.select_one(".Caption")
    return gq_text_new_line(caption_element) if caption_element else None


def construct_json_response(
    typename: MediaType,
    media_url: str | list[str] | None,
    username: str | None,
    caption: str | None,
    video_blocked: bool,
) -> bytes:
    return orjson.dumps({
        "shortcode_media": {
            "owner": {"username": username},
            "node": {"__typename": typename.value, "display_url": media_url},
            "edge_media_to_caption": {"edges": [{"node": {"text": caption}}]},
            "dimensions": {"height": None, "width": None},
            "video_blocked": video_blocked,
        }
    })


async def _get_response(url: str, proxy: str | None = None) -> httpx.Response | None:
    try:
        async with httpx.AsyncClient(
            headers=HEADERS, timeout=TIMEOUT, http2=True, proxy=proxy
        ) as session:
            response = await session.get(url)
            if response.status_code == 200 and response.text:
                return response
    except httpx.ConnectError as err:
        log.error("Failed to get response for URL %s with proxy %s: %s", url, proxy, err)
        msg = f"Connection error while fetching data from {url}: {err}"
        raise InstaError(msg) from err
    return None


async def get_response(url: str) -> httpx.Response | None:
    proxies = ConfigManager.get("korone", "PROXIES")

    for _ in range(3):
        response = await _get_response(url)
        if response is not None:
            return response

    for proxy in proxies:
        for _ in range(3):
            response = await _get_response(url, proxy)
            if response is not None:
                return response
    return None


def get_time_slice(response: httpx.Response) -> dict[str, Any] | None:
    time_slice = re.findall(r'<script>(requireLazy\(\["TimeSliceImpl".*)<\/script>', response.text)
    if time_slice:
        tokenized = esprima.tokenize(time_slice[0])
        for token in tokenized:
            if "shortcode_media" in token.value:
                try:
                    return orjson.loads(orjson.loads(token.value))
                except orjson.JSONDecodeError as err:
                    log.error(
                        "Failed to parse data from TimeSliceImpl for %s: %s", response.url, err
                    )
                    msg = f"Error while parsing TimeSliceImpl data: {err}"
                    raise InstaError(msg) from err
    return None


async def get_embed_html_data(response: httpx.Response, post_id: str) -> dict[str, Any] | None:
    try:
        content = response.text
        embed_html = parse_embed_html(content)
        embed_html_data = orjson.loads(embed_html)
        video_blocked = embed_html_data.get("shortcode_media", {}).get("video_blocked")
        username = embed_html_data.get("shortcode_media", {}).get("owner", {}).get("username")

        if video_blocked or not username:
            gql_data = await parse_gql_data(post_id)
            if gql_data and gql_data.get("data"):
                return gql_data.get("data")
    except (InstaError, orjson.JSONDecodeError) as err:
        log.error("Failed to parse data for post ID %s: %s", post_id, err)
        msg = f"Error while parsing embed HTML data for post ID {post_id}: {err}"
        raise InstaError(msg) from err
    return embed_html_data


async def _parse_gql_data(
    url: str, params: dict[str, Any], proxy: str | None = None
) -> httpx.Response | None:
    headers = {**HEADERS, "Referer": url}
    try:
        async with httpx.AsyncClient(
            headers=headers, timeout=TIMEOUT, http2=True, proxies=proxy
        ) as session:
            response = await session.get("https://www.instagram.com/graphql/query/", params=params)
            if response.status_code == 200 and response.content:
                return response
    except httpx.ConnectError as err:
        log.error("Failed to get response for URL %s with proxy %s: %s", url, proxy, err)
        msg = f"Connection error while fetching GraphQL data from {url}: {err}"
        raise InstaError(msg) from err
    return None


async def parse_gql_data(post_id: str) -> dict[str, Any] | None:
    url = f"https://www.instagram.com/p/{post_id}/"
    params = {
        "av": "0",
        "__d": "www",
        "__user": "0",
        "__a": "1",
        "__req": "k",
        "__hs": "19888.HYP:instagram_web_pkg.2.1..0.0",
        "dpr": "2",
        "__ccg": "UNKNOWN",
        "__rev": "1014227545",
        "__s": "trbjos:n8dn55:yev1rm",
        "__hsi": "7380500578385702299",
        "__dyn": "7xeUjG1mxu1syUbFp40NonwgU7SbzEdF8aUco2qwJw5ux609vCwjE1xoswaq0yE6ucw5Mx62G5UswoE"
        "cE7O2l0Fwqo31w9a9wtUd8-U2zxe2GewGw9a362W2K0zK5o4q3y1Sx-0iS2Sq2-azo7u3C2u2J0bS1LwTwKG1pg2"
        "fwxyo6O1FwlEcUed6goK2O4UrAwCAxW6Uf9EObzVU8U",
        "__csr": "n2Yfg_5hcQAG5mPtfEzil8Wn-DpKGBXhdczlAhrK8uHBAGuKCJeCieLDyExenh68aQAKta8p8ShogKk"
        "F5yaUBqCpF9XHmmhoBXyBKbQp0HCwDjqoOepV8Tzk8xeXqAGFTVoCciGaCgvGUtVU-u5Vp801nrEkO0rC58xw41g"
        "0VW07ISyie2W1v7F0CwYwwwvEkw8K5cM0VC1dwdi0hCbc094w6MU1xE02lzw",
        "__comet_req": "7",
        "lsd": "AVoPBTXMX0Y",
        "jazoest": "2882",
        "__spin_r": "1014227545",
        "__spin_b": "trunk",
        "__spin_t": "1718406700",
        "fb_api_caller_class": "RelayModern",
        "fb_api_req_friendly_name": "PolarisPostActionLoadPostQueryQuery",
        "variables": f'{
            {
                "shortcode": f"{post_id}",
                "fetch_comment_count": "40",
                "parent_comment_count": "24",
                "child_comment_count": "3",
                "fetch_like_count": "10",
                "fetch_tagged_user_count": "null",
                "fetch_preview_comment_count": "2",
                "has_threaded_comments": "true",
                "hoisted_comment_id": "null",
                "hoisted_reply_id": "null",
            }
        }',
        "server_timestamps": "true",
        "doc_id": "25531498899829322",
    }
    proxies = ConfigManager.get("korone", "PROXIES")

    for _ in range(3):
        response = await _parse_gql_data(url, params)
        if response is not None:
            gql_value = await response.aread()
            return orjson.loads(gql_value) if gql_value else None

    for proxy in proxies:
        for _ in range(3):
            response = await _parse_gql_data(url, params, proxy)
            if response is not None:
                gql_value = await response.aread()
                return orjson.loads(gql_value) if gql_value else None
    return None


async def get_data(post_id: str) -> dict[str, Any] | None:
    url = f"https://www.instagram.com/p/{post_id}/embed/captioned/"
    response = await get_response(url)

    if not response or response.status_code != 200:
        return None

    time_slice = get_time_slice(response)
    if time_slice:
        return time_slice.get("gql_data")

    return await get_embed_html_data(response, post_id)


@cache(ttl=timedelta(weeks=1))
async def get_instagram_data(post_id: str) -> InstaData:
    data = await fetch_data(post_id)
    return process_data(data, post_id)


async def fetch_data(post_id: str) -> dict[str, Any] | None:
    try:
        return await get_data(post_id)
    except (InstaError, httpx.ConnectError) as err:
        log.error("Failed to fetch data for post ID %s: %s", post_id, err)
        msg = f"Failed to fetch data for post ID {post_id}: {err}"
        raise InstaError(msg) from err


def process_data(data: dict[str, Any] | None, post_id: str) -> InstaData:
    if not data:
        msg = f"No data found for post ID {post_id}"
        raise NotFoundError(msg)

    shortcode_media = data["shortcode_media"]
    if not shortcode_media:
        shortcode_media = data["xdt_shortcode_media"]
        if not shortcode_media:
            msg = f"No shortcode media found for post ID: {post_id}"
            raise NotFoundError(msg)

    username = shortcode_media["owner"]["username"]
    caption_edges = shortcode_media["edge_media_to_caption"]["edges"]
    caption = caption_edges[0]["node"]["text"] if caption_edges else None

    media = shortcode_media.get("edge_sidecar_to_children", {}).get("edges", [shortcode_media])
    medias = [
        Media(
            type_name=MediaType(m.get("node", m)["__typename"]),
            url=m.get("node", m).get("video_url", m.get("node", m).get("display_url")),
        )
        for m in media
    ]

    return InstaData(
        post_id=post_id,
        username=username,
        caption=caption,
        medias=medias,
    )

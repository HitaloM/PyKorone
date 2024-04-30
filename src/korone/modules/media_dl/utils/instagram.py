# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

import re
from dataclasses import dataclass
from typing import Any, Literal

import aiohttp
import esprima
import orjson
from bs4 import BeautifulSoup, NavigableString, PageElement, Tag

from korone.utils.logging import log

TIMEOUT: int = 20
HEADERS: dict[str, str] = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,"
    "image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "close",
    "Sec-Fetch-Mode": "navigate",
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
}


class InstaError(Exception):
    pass


class NotFoundError(InstaError):
    pass


@dataclass
class Media:
    type_name: str
    url: str


@dataclass
class InstaData:
    post_id: str
    username: str
    caption: str
    medias: list[Media]


class InstagramDataFetcher:
    def __init__(self) -> None:
        self.html_parser = InstagramHtmlParser()

    async def get_data(self, post_id: str) -> dict[str, Any] | None:
        url = f"https://www.instagram.com/p/{post_id}/embed/captioned"
        response = await self.get_response(url)

        if response is None:
            return None

        time_slice = await self.get_time_slice(response)
        if time_slice:
            return time_slice.get("gql_data")

        return await self.get_embed_html_data(response, post_id)

    @staticmethod
    async def get_response(url: str) -> aiohttp.ClientResponse | None:
        for _ in range(3):
            try:
                async with aiohttp.ClientSession() as session:
                    response = await session.get(url, headers=HEADERS, timeout=TIMEOUT)
                    if response.status == 200 and response.text:
                        return response
            except aiohttp.ClientError as e:
                log.error("Failed to get response: %s", e)
        return None

    @staticmethod
    async def get_time_slice(response: aiohttp.ClientResponse) -> dict[str, Any] | None:
        time_slice = re.findall(
            r'<script>(requireLazy\(\["TimeSliceImpl".*)<\/script>', await response.text()
        )
        if time_slice:
            tokenized = esprima.tokenize(time_slice[0])
            for token in tokenized:
                if "shortcode_media" in token.value:
                    try:
                        return orjson.loads(orjson.loads(token.value))
                    except orjson.JSONDecodeError as err:
                        log.error("Failed to parse data from TimeSliceImpl: %s", err)
                        raise InstaError(err)
        return None

    async def get_embed_html_data(
        self, response: aiohttp.ClientResponse, post_id: str
    ) -> dict[str, Any] | None:
        try:
            content = await response.text()
            embed_html = self.html_parser.parse_embed_html(content)
            embed_html_data = orjson.loads(embed_html)
            video_blocked = embed_html_data.get("shortcode_media", {}).get("video_blocked")
            username = embed_html_data.get("shortcode_media", {}).get("owner", {}).get("username")

            if video_blocked or not username:
                gql_data = await self.parse_gql_data(post_id)
                if gql_data and gql_data.get("data"):
                    return gql_data.get("data")

            return embed_html_data
        except (InstaError, orjson.JSONDecodeError) as err:
            log.error("Failed to parse data: %s", err)
            raise err

    @staticmethod
    async def parse_gql_data(post_id: str) -> dict[str, Any] | None:
        headers = {**HEADERS, "Referer": f"https://www.instagram.com/p/{post_id}/"}
        params = {
            "query_hash": "b3055c01b4b222b8a47dc12b090e4e64",
            "variables": f'{{"shortcode":"{post_id}"}}',
        }
        async with aiohttp.ClientSession() as session:
            response = await session.get(
                "https://www.instagram.com/graphql/query/",
                headers=headers,
                params=params,
                timeout=TIMEOUT,
            )
            if response.status != 200:
                raise InstaError(f"Request failed with status {response.status}")

            gql_value = await response.content.read()
            return orjson.loads(gql_value) if gql_value else None


class InstagramHtmlParser:
    def gq_text_new_line(self, s: Tag | PageElement | None) -> str:
        if s is None:
            return ""

        result = [
            c
            if isinstance(c, NavigableString)
            else "\n"
            if getattr(c, "name", "") == "br"
            else self.gq_text_new_line(c)
            for c in getattr(s, "children", [])
        ]

        return "".join(result)

    def parse_embed_html(self, embed_html: str) -> bytes:
        doc = BeautifulSoup(embed_html, "lxml")
        typename, media_url = self.get_typename_and_media_url(doc)
        username = self.get_username(doc)
        caption = self.get_caption(doc)
        video_blocked = "WatchOnInstagram" in embed_html

        return self.construct_json_response(typename, media_url, username, caption, video_blocked)

    @staticmethod
    def get_typename_and_media_url(
        doc: BeautifulSoup,
    ) -> tuple[Literal["GraphVideo", "GraphImage"], str | list[str] | None]:
        typename = "GraphImage"
        embed_media = doc.select_one(".EmbeddedMediaImage")
        if embed_media is None:
            typename = "GraphVideo"
            embed_media = doc.select_one(".EmbeddedMediaVideo")
        media_url = embed_media.get("src") if embed_media else None
        return typename, media_url

    @staticmethod
    def get_username(doc: BeautifulSoup) -> str | None:
        username_element = doc.select_one(".UsernameText")
        return username_element.get_text() if username_element else None

    def get_caption(self, doc: BeautifulSoup):
        caption_comments = doc.select_one(".CaptionComments")
        if caption_comments:
            caption_comments.decompose()
        caption_username = doc.select_one(".CaptionUsername")
        if caption_username:
            caption_username.decompose()
        caption_element = doc.select_one(".Caption")
        return self.gq_text_new_line(caption_element) if caption_element else None

    @staticmethod
    def construct_json_response(
        typename: str,
        media_url: str | list[str] | None,
        username: str | None,
        caption: str | None,
        video_blocked: bool,
    ) -> bytes:
        return orjson.dumps({
            "shortcode_media": {
                "owner": {"username": username},
                "node": {"__typename": typename, "display_url": media_url},
                "edge_media_to_caption": {"edges": [{"node": {"text": caption}}]},
                "dimensions": {"height": None, "width": None},
                "video_blocked": video_blocked,
            }
        })


class GetInstagram:
    def __init__(self) -> None:
        self.data_fetcher = InstagramDataFetcher()

    async def get_data(self, post_id: str) -> InstaData:
        data = await self.fetch_data(post_id)
        return self.process_data(data, post_id)

    async def fetch_data(self, post_id: str) -> dict[str, Any]:
        data = await self.data_fetcher.get_data(post_id)
        if data is None:
            raise NotFoundError("data not found")

        item = data.get("shortcode_media")
        if item is None:
            raise NotFoundError("shortcode_media not found")
        return item

    def process_data(self, item: dict[str, Any], post_id: str):
        media = self.get_media(item)

        username = item["owner"]["username"]
        caption = item["edge_media_to_caption"]["edges"][0]["node"]["text"].strip()

        return InstaData(
            post_id=post_id,
            username=username,
            caption=caption,
            medias=media,
        )

    @staticmethod
    def get_media(item: dict[str, Any]) -> list[Media]:
        media = item.get("edge_sidecar_to_children", {}).get("edges", [item])

        medias = []
        for m in media:
            if "node" in m:
                m = m["node"]
            media_url = m.get("video_url")
            if media_url is None:
                media_url = m.get("display_url")
            medias.append(Media(type_name=m["__typename"], url=media_url))

        return medias

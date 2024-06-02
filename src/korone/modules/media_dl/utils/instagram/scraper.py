# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import re
from dataclasses import dataclass
from datetime import timedelta
from typing import Any, Literal

import esprima
import httpx
import orjson
from bs4 import BeautifulSoup, NavigableString, PageElement, Tag

from korone import cache
from korone.config import ConfigManager
from korone.modules.media_dl.utils.instagram.constants import HEADERS, TIMEOUT
from korone.utils.logging import log


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
    caption: str | None
    medias: list[Media]


class InstagramHtmlParser:
    def __init__(self) -> None:
        self.html_parser = BeautifulSoup

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
        doc = self.html_parser(embed_html, "lxml")
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

    def get_caption(self, doc: BeautifulSoup) -> str | None:
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


class InstagramDataFetcher:
    def __init__(self) -> None:
        self.html_parser = InstagramHtmlParser()

    async def get_data(self, post_id: str) -> dict[str, Any] | None:
        url = f"https://www.instagram.com/p/{post_id}/embed/captioned/"
        response = await self.get_response(url)

        if not response or response.status_code != 200:
            return None

        time_slice = await self.get_time_slice(response)
        if time_slice:
            return time_slice.get("gql_data")

        return await self.get_embed_html_data(response, post_id)

    @staticmethod
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

    async def get_response(self, url: str) -> httpx.Response | None:
        proxies = ConfigManager.get("korone", "PROXIES")

        for _ in range(3):
            response = await self._get_response(url)
            if response is not None:
                return response

        for proxy in proxies:
            for _ in range(3):
                response = await self._get_response(url, proxy)
                if response is not None:
                    return response
        return None

    @staticmethod
    async def get_time_slice(response: httpx.Response) -> dict[str, Any] | None:
        time_slice = re.findall(
            r'<script>(requireLazy\(\["TimeSliceImpl".*)<\/script>', response.text
        )
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

    async def get_embed_html_data(
        self, response: httpx.Response, post_id: str
    ) -> dict[str, Any] | None:
        try:
            content = response.text
            embed_html = self.html_parser.parse_embed_html(content)
            embed_html_data = orjson.loads(embed_html)
            video_blocked = embed_html_data.get("shortcode_media", {}).get("video_blocked")
            username = embed_html_data.get("shortcode_media", {}).get("owner", {}).get("username")

            if video_blocked or not username:
                gql_data = await self.parse_gql_data(post_id)
                if gql_data and gql_data.get("data"):
                    return gql_data.get("data")
        except (InstaError, orjson.JSONDecodeError) as err:
            log.error("Failed to parse data for post ID %s: %s", post_id, err)
            msg = f"Error while parsing embed HTML data for post ID {post_id}: {err}"
            raise InstaError(msg) from err
        return embed_html_data

    @staticmethod
    async def _parse_gql_data(
        url: str, params: dict[str, Any], proxy: str | None = None
    ) -> httpx.Response | None:
        headers = {**HEADERS, "Referer": url}
        try:
            async with httpx.AsyncClient(
                headers=headers, timeout=TIMEOUT, http2=True, proxies=proxy
            ) as session:
                response = await session.get(
                    "https://www.instagram.com/graphql/query/", params=params
                )
                if response.status_code == 200 and response.content:
                    return response
        except httpx.ConnectError as err:
            log.error("Failed to get response for URL %s with proxy %s: %s", url, proxy, err)
            msg = f"Connection error while fetching GraphQL data from {url}: {err}"
            raise InstaError(msg) from err
        return None

    async def parse_gql_data(self, post_id: str) -> dict[str, Any] | None:
        url = f"https://www.instagram.com/p/{post_id}/"
        params = {
            "query_hash": "b3055c01b4b222b8a47dc12b090e4e64",
            "variables": f'{{"shortcode":"{post_id}"}}',
        }
        proxies = ConfigManager.get("korone", "PROXIES")

        for _ in range(3):
            response = await self._parse_gql_data(url, params)
            if response is not None:
                gql_value = await response.aread()
                return orjson.loads(gql_value) if gql_value else None

        for proxy in proxies:
            for _ in range(3):
                response = await self._parse_gql_data(url, params, proxy)
                if response is not None:
                    gql_value = await response.aread()
                    return orjson.loads(gql_value) if gql_value else None
        return None


class GetInstagram:
    def __init__(self) -> None:
        self.data_fetcher = InstagramDataFetcher()

    @cache(ttl=timedelta(days=1), key="insta_data:{post_id}")
    async def get_data(self, post_id: str) -> InstaData:
        data = await self.fetch_data(post_id)
        return self.process_data(data, post_id)

    async def fetch_data(self, post_id: str) -> dict[str, Any] | None:
        try:
            return await self.data_fetcher.get_data(post_id)
        except (InstaError, httpx.ConnectError) as err:
            log.error("Failed to fetch data for post ID %s: %s", post_id, err)
            msg = f"Failed to fetch data for post ID {post_id}: {err}"
            raise InstaError(msg) from err

    @staticmethod
    def process_data(data: dict[str, Any] | None, post_id: str) -> InstaData:
        if not data:
            msg = f"No data found for post ID {post_id}"
            raise NotFoundError(msg)

        shortcode_media = data["shortcode_media"]
        username = shortcode_media["owner"]["username"]
        caption_edges = shortcode_media["edge_media_to_caption"]["edges"]
        caption = caption_edges[0]["node"]["text"] if caption_edges else None

        media = shortcode_media.get("edge_sidecar_to_children", {}).get("edges", [shortcode_media])
        medias = [
            Media(
                type_name=m.get("node", m)["__typename"],
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
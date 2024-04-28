# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

import re
from dataclasses import dataclass
from datetime import timedelta
from typing import Any

import aiohttp
import esprima
import orjson
from bs4 import BeautifulSoup, NavigableString, Tag

from korone import cache
from korone.utils.http import http_session
from korone.utils.logging import log

TIMEOUT: int = 10
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


class GetInstagram:
    async def _get_data(self, post_id: str) -> dict[str, Any] | None:
        url = f"https://www.instagram.com/p/{post_id}/embed/captioned"
        response = None
        for _ in range(3):
            try:
                response = await http_session.get(url, headers=HEADERS, timeout=TIMEOUT)
                if response.status == 200 and response.text:
                    break
            except aiohttp.ClientError as e:
                log.error("Failed to get response: %s", e)
                continue

        if response is None:
            return None

        time_slice = re.findall(
            r'<script>(requireLazy\(\["TimeSliceImpl".*)<\/script>', await response.text()
        )
        if time_slice:
            tokenized = esprima.tokenize(time_slice[0])
            for token in tokenized:
                if "shortcode_media" in token.value:
                    try:
                        time_slice = orjson.loads(orjson.loads(token.value))
                        log.debug("Data parsed from TimeSliceImpl for postID %s", post_id)
                        return time_slice.get("gql_data")
                    except orjson.JSONDecodeError as err:
                        log.error(
                            "Failed to parse data from TimeSliceImpl for postID %s: %s",
                            post_id,
                            err,
                        )
                        raise InstaError(err)

        try:
            content = await response.text()
            embed_html = self._parse_embed_html(content)
        except InstaError as err:
            log.error("Failed to parse data from ParseEmbedHTML: %s", err)
            raise err

        try:
            embed_html_data = orjson.loads(embed_html)
        except orjson.JSONDecodeError as err:
            log.error("Failed to parse bytes: %s", err)
            raise err

        smedia = embed_html_data.get("shortcode_media")
        video_blocked = smedia.get("video_blocked")
        username = smedia.get("owner", {}).get("username")

        if video_blocked or not username:
            try:
                gql_value = await self._parse_gql_data(post_id)
                if isinstance(gql_value, str):
                    gql_value_bytes = gql_value.encode("utf-8")
                    gql_data = orjson.loads(gql_value_bytes)
                    if gql_data.get("data"):
                        log.debug("Data parsed from parseGQLData: %s", gql_data.get("data"))
                        return gql_data.get("data")
            except InstaError as err:
                log.error("Failed to parse data from parseGQLData: %s", err)
                raise err

        if not username:
            raise NotFoundError("Username not found in embed_html_data")

        try:
            embed_html_data = orjson.loads(embed_html)
            log.debug("Data parsed from ParseEmbedHTML: %s", embed_html_data)
            return embed_html_data
        except orjson.JSONDecodeError as err:
            log.error("Failed to re-parse bytes: %s", err)
            raise err

    def _gq_text_new_line(self, s: Tag | None) -> str:
        result = []
        if s is None:
            return ""

        for c in s.children:
            if isinstance(c, NavigableString):
                result.append(c)
            elif isinstance(c, Tag):
                if c.name == "br":
                    result.append("\n")
                else:
                    result.append(self._gq_text_new_line(c))

        return "".join(result)

    def _parse_embed_html(self, embed_html: Any) -> bytes:
        doc = BeautifulSoup(embed_html, "lxml")

        typename = "GraphImage"
        embed_media = doc.select_one(".EmbeddedMediaImage")
        if embed_media is None:
            typename = "GraphVideo"
            embed_media = doc.select_one(".EmbeddedMediaVideo")
        media_url = embed_media.get("src") if embed_media else None

        username_element = doc.select_one(".UsernameText")
        username = username_element.get_text() if username_element else None

        caption_comments = doc.select_one(".CaptionComments")
        if caption_comments:
            caption_comments.decompose()
        caption_username = doc.select_one(".CaptionUsername")
        if caption_username:
            caption_username.decompose()
        caption = (
            self._gq_text_new_line(doc.select_one(".Caption"))
            if doc.select_one(".Caption")
            else None
        )

        video_blocked = "WatchOnInstagram" in embed_html

        return orjson.dumps({
            "shortcode_media": {
                "owner": {"username": username},
                "node": {"__typename": typename, "display_url": media_url},
                "edge_media_to_caption": {"edges": [{"node": {"text": caption}}]},
                "dimensions": {"height": None, "width": None},
                "video_blocked": video_blocked,
            }
        })

    @staticmethod
    async def _parse_gql_data(post_id: str) -> bytes | None:
        headers = {**HEADERS, "Referer": f"https://www.instagram.com/p/{post_id}/"}
        params = {
            "query_hash": "b3055c01b4b222b8a47dc12b090e4e64",
            "variables": f'{{"shortcode":"{post_id}"}}',
        }
        response = await http_session.get(
            "https://www.instagram.com/graphql/query/",
            headers=headers,
            params=params,
            timeout=TIMEOUT,
        )
        if response.status != 200:
            raise InstaError(f"Request failed with status {response.status}")

        return await response.content.read()

    async def get_data(self, post_id: str) -> InstaData:
        cache_insta_data = await cache.get(post_id)
        if cache_insta_data is not None:
            try:
                cache_data = orjson.loads(cache_insta_data)
                insta_data = InstaData(
                    post_id=cache_data.get("post_id"),
                    username=cache_data.get("username"),
                    caption=cache_data.get("caption"),
                    medias=[Media(**m) for m in cache_data.get("medias")],
                )
                log.debug("Data loaded from cache for postID: %s", post_id)
                return insta_data
            except InstaError as err:
                raise err

        data = await self._get_data(post_id)

        if data is None:
            raise InstaError("data is None")

        item = data.get("shortcode_media")
        if item is None:
            raise NotFoundError("shortcode_media not found")

        media = [item]
        if "edge_sidecar_to_children" in item:
            media = item["edge_sidecar_to_children"]["edges"]

        medias = []
        for m in media:
            if "node" in m:
                m = m["node"]
            media_url = m.get("video_url")
            if media_url is None:
                media_url = m.get("display_url")
            medias.append(Media(type_name=m["__typename"], url=media_url))

        insta_data = InstaData(
            post_id=post_id,
            username=item["owner"]["username"],
            caption=item["edge_media_to_caption"]["edges"][0]["node"]["text"].strip(),
            medias=medias,
        )

        try:
            await cache.set(
                key=post_id,
                value=orjson.dumps(
                    {
                        "post_id": insta_data.post_id,
                        "username": insta_data.username,
                        "caption": insta_data.caption,
                        "medias": [m.__dict__ for m in insta_data.medias],
                    },
                ),
                expire=timedelta(days=1),
            )
        except BaseException as err:
            log.error("Failed to set cache for postID %s: %s", post_id, err)
            raise InstaError(err)

        return insta_data

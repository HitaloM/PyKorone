from typing import TYPE_CHECKING, Any
from urllib.parse import urljoin

import aiohttp

from korone.logger import get_logger
from korone.modules.medias.download import DEFAULT_MEDIA_HEADERS

from . import parser
from .constants import MAX_REDIRECTS, TIKTOK_MEDIA_HEADERS, TIKTOK_TIMEOUT, TIKTOK_WEB_HEADERS, WEB_VIDEO_DETAIL_URL

if TYPE_CHECKING:
    from korone.http import HttpClient

logger = get_logger(__name__)


class TikTokClient:
    __slots__ = ("_http",)

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    async def resolve_redirect_url(self, url: str) -> str | None:
        try:
            async with self._http.session.get(
                url,
                timeout=TIKTOK_TIMEOUT,
                headers=DEFAULT_MEDIA_HEADERS | TIKTOK_WEB_HEADERS,
                allow_redirects=True,
                max_redirects=MAX_REDIRECTS,
            ) as response:
                return str(response.url)
        except (aiohttp.ClientError, aiohttp.TooManyRedirects) as error:
            await logger.awarning("[TikTok] Redirect resolution failed", error=str(error), url=url)
            return None

    async def fetch_item_struct(self, post_id: str) -> dict[str, Any] | None:
        try:
            async with self._http.session.get(
                WEB_VIDEO_DETAIL_URL.format(post_id=post_id),
                timeout=TIKTOK_TIMEOUT,
                headers=DEFAULT_MEDIA_HEADERS | TIKTOK_WEB_HEADERS,
            ) as response:
                if response.status != 200:
                    await logger.adebug("[TikTok] Non-200 page response", status=response.status, post_id=post_id)
                    return None
                html_content = await response.text()
        except (aiohttp.ClientError, UnicodeDecodeError) as error:
            await logger.awarning("[TikTok] Failed to fetch post page", error=str(error), post_id=post_id)
            return None

        payload = parser.extract_universal_data_payload(html_content)
        if not payload:
            await logger.adebug("[TikTok] Universal payload not found", post_id=post_id)
            return None
        item_struct = parser.extract_item_struct(payload)
        if not item_struct:
            await logger.adebug("[TikTok] itemStruct not found", post_id=post_id)
            return None
        return item_struct

    async def resolve_media_url(self, url: str) -> str | None:
        try:
            async with self._http.session.get(
                url, timeout=TIKTOK_TIMEOUT, headers=dict(TIKTOK_MEDIA_HEADERS), allow_redirects=False, cookies={}
            ) as response:
                if response.status in {301, 302} and (location := response.headers.get("Location")):
                    return urljoin(str(response.url), location)
                return url
        except aiohttp.ClientError as error:
            await logger.adebug("[TikTok] Could not resolve media redirect", error=str(error), url=url)
            return None

from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

import aiohttp

from korone.logger import get_logger
from korone.modules.medias.utils.provider_base import MediaProvider
from korone.utils.aiohttp_session import HTTPClient

from . import parser
from .constants import MAX_REDIRECTS, TIKTOK_MEDIA_HEADERS, TIKTOK_WEB_HEADERS, WEB_VIDEO_DETAIL_URL

logger = get_logger(__name__)

_REDIRECT_STATUSES = {301, 302}


async def resolve_redirect_url(url: str) -> str | None:
    try:
        session = await HTTPClient.get_session()
        async with session.get(
            url,
            timeout=MediaProvider._DEFAULT_TIMEOUT,
            headers={**MediaProvider._DEFAULT_HEADERS, **TIKTOK_WEB_HEADERS},
            allow_redirects=True,
            max_redirects=MAX_REDIRECTS,
        ) as response:
            return str(response.url)
    except (aiohttp.ClientError, aiohttp.TooManyRedirects) as exc:
        await logger.aerror("[TikTok] Redirect resolution failed", error=str(exc), url=url)
        return None


async def fetch_item_struct(post_id: str) -> dict[str, Any] | None:
    page_url = WEB_VIDEO_DETAIL_URL.format(post_id=post_id)

    try:
        session = await HTTPClient.get_session()
        async with session.get(
            page_url,
            timeout=MediaProvider._DEFAULT_TIMEOUT,
            headers={**MediaProvider._DEFAULT_HEADERS, **TIKTOK_WEB_HEADERS},
        ) as response:
            if response.status != 200:
                await logger.adebug("[TikTok] Non-200 page response", status=response.status, post_id=post_id)
                return None
            html_content = await response.text()
    except (aiohttp.ClientError, UnicodeDecodeError) as exc:
        await logger.aerror("[TikTok] Failed to fetch post page", error=str(exc), post_id=post_id)
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


async def resolve_media_url(url: str) -> str | None:
    try:
        session = await HTTPClient.get_session()
        async with session.get(
            url,
            timeout=MediaProvider._DEFAULT_TIMEOUT,
            headers=dict(TIKTOK_MEDIA_HEADERS),
            allow_redirects=False,
            cookies={},
        ) as response:
            if response.status in _REDIRECT_STATUSES:
                location = response.headers.get("Location")
                if isinstance(location, str) and location:
                    return urljoin(str(response.url), location)
            return url
    except aiohttp.ClientError as exc:
        await logger.adebug("[TikTok] Could not resolve media redirect", error=str(exc), url=url)
        return None

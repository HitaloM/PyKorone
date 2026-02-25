from __future__ import annotations

import gzip
from typing import Any, cast

import aiohttp
import orjson

from korone.logger import get_logger
from korone.modules.medias.utils.platforms import MediaProvider
from korone.utils.aiohttp_session import HTTPClient

from .constants import TIKTOK_API_HEADERS, TIKTOK_FEED_API, TIKTOK_QUERY_PARAMS
from .parser import extract_first_aweme

logger = get_logger(__name__)


async def resolve_redirect_url(url: str) -> str | None:
    try:
        session = await HTTPClient.get_session()
        async with session.get(
            url,
            timeout=MediaProvider._DEFAULT_TIMEOUT,
            headers=MediaProvider._DEFAULT_HEADERS,
            allow_redirects=True,
            max_redirects=2,
        ) as response:
            return str(response.url)
    except aiohttp.ClientError as exc:
        await logger.aerror("[TikTok] Redirect resolution failed", error=str(exc), url=url)
        return None


async def fetch_aweme(post_id: str) -> dict[str, Any] | None:
    params = {**TIKTOK_QUERY_PARAMS, "aweme_id": post_id}
    headers = {**MediaProvider._DEFAULT_HEADERS, **TIKTOK_API_HEADERS}

    for method in ("OPTIONS", "GET"):
        try:
            session = await HTTPClient.get_session()
            async with session.request(
                method, TIKTOK_FEED_API, timeout=MediaProvider._DEFAULT_TIMEOUT, headers=headers, params=params
            ) as response:
                if response.status != 200:
                    await logger.adebug(
                        "[TikTok] Non-200 feed response", method=method, status=response.status, post_id=post_id
                    )
                    continue

                payload = load_feed_payload(await response.read())
        except (
            aiohttp.ClientError,
            aiohttp.ContentTypeError,
            orjson.JSONDecodeError,
            UnicodeDecodeError,
            OSError,
        ) as exc:
            await logger.aerror("[TikTok] Feed request failed", method=method, error=str(exc), post_id=post_id)
            continue

        if not isinstance(payload, dict):
            continue

        aweme = extract_first_aweme(payload, post_id)
        if aweme:
            return cast("dict[str, Any]", aweme)

    return None


def load_feed_payload(payload: bytes) -> Any:  # noqa: ANN401
    # Some TikTok edges return gzipped bytes without a matching response header.
    if is_gzip_payload(payload):
        payload = gzip.decompress(payload)
    return orjson.loads(payload)


def is_gzip_payload(payload: bytes) -> bool:
    return len(payload) >= 2 and payload[0] == 0x1F and payload[1] == 0x8B

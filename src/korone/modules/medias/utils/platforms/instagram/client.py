from __future__ import annotations

import aiohttp

from korone.logger import get_logger
from korone.modules.medias.utils.provider_base import MediaProvider
from korone.utils.aiohttp_session import HTTPClient

from . import parser

logger = get_logger(__name__)


async def get_instafix_data(instafix_url: str) -> dict[str, str] | None:
    try:
        session = await HTTPClient.get_session()
        async with session.get(
            instafix_url,
            timeout=MediaProvider._DEFAULT_TIMEOUT,
            headers=MediaProvider._DEFAULT_HEADERS,
            allow_redirects=True,
        ) as response:
            if response.status != 200:
                await logger.adebug("[Instagram] Non-200 response", status=response.status, url=instafix_url)
                return None

            text = await response.text()
            scraped = parser.scrape_instafix_data(text)
            if not scraped.get("media_url"):
                return None

            media_url = parser.ensure_url_scheme(scraped["media_url"])
            async with session.get(media_url, allow_redirects=True) as media_response:
                if media_response.status != 200:
                    await logger.adebug(
                        "[Instagram] Media redirect failed", status=media_response.status, url=media_url
                    )
                    return None

                media_url = str(media_response.url)
                await media_response.release()

            scraped["media_url"] = media_url
            scraped["media_type"] = scraped.get("type", "")
            scraped.pop("type", None)
            return scraped
    except (aiohttp.ClientError, aiohttp.ContentTypeError) as exc:
        await logger.aerror("[Instagram] Fetch failed", error=str(exc), url=instafix_url)
        return None


async def download_media(url: str) -> bytes | None:
    try:
        session = await HTTPClient.get_session()
        async with session.get(
            url, timeout=MediaProvider._DEFAULT_TIMEOUT, headers=MediaProvider._DEFAULT_HEADERS
        ) as response:
            if response.status != 200:
                await logger.adebug("[Instagram] Failed to download media", status=response.status, url=url)
                return None
            return await response.read()
    except aiohttp.ClientError as exc:
        await logger.aerror("[Instagram] Media download error", error=str(exc))
        return None

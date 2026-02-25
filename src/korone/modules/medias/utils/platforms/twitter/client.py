from __future__ import annotations

from typing import Any, cast

import aiohttp
import orjson

from korone.logger import get_logger
from korone.modules.medias.utils.provider_base import MediaProvider
from korone.utils.aiohttp_session import HTTPClient

logger = get_logger(__name__)


async def fetch_json(url: str) -> dict[str, Any] | None:
    try:
        session = await HTTPClient.get_session()
        async with session.get(
            url, timeout=MediaProvider._DEFAULT_TIMEOUT, headers=MediaProvider._DEFAULT_HEADERS
        ) as response:
            if response.status != 200:
                await logger.adebug("[FXTwitter] Non-200 response", status=response.status, url=url)
                return None

            data = await response.json(loads=orjson.loads)
            return cast("dict[str, Any]", data)
    except (aiohttp.ClientError, aiohttp.ContentTypeError) as exc:
        await logger.aerror("[FXTwitter] Request error", error=str(exc), url=url)
        return None

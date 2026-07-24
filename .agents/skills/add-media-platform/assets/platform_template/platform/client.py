from typing import Any

import aiohttp

from korone.logger import get_logger
from korone.modules.medias.utils.parsing import dict_or_empty
from korone.utils.aiohttp_session import HTTPClient

from .constants import API_URL, REQUEST_TIMEOUT

logger = get_logger(__name__)


async def fetch_post(post_id: str, *, headers: dict[str, str]) -> dict[str, Any] | None:
    session = await HTTPClient.get_session()

    try:
        async with session.get(API_URL.format(post_id=post_id), headers=headers, timeout=REQUEST_TIMEOUT) as response:
            if response.status != 200:
                await logger.adebug("[Example] Post request failed", post_id=post_id, status=response.status)
                return None

            payload = dict_or_empty(await response.json())
            return payload or None
    except (TimeoutError, aiohttp.ClientError, ValueError) as error:
        await logger.awarning("[Example] Post request error", post_id=post_id, error=str(error))
        return None

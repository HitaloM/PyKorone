from typing import Any, Final

import aiohttp
import orjson

from korone.logger import get_logger
from korone.modules.medias.utils.parsing import dict_or_empty
from korone.utils.aiohttp_session import HTTPClient, RetryPolicy

from .constants import API_URL, REQUEST_TIMEOUT, RETRYABLE_STATUSES

logger = get_logger(__name__)

_RETRY_POLICY: Final[RetryPolicy] = RetryPolicy(
    attempts=3,
    timeout=REQUEST_TIMEOUT,
    retryable_statuses=RETRYABLE_STATUSES,
    backoff_seconds=(0.8, 1.6),
    jitter_seconds=0.25,
    buffer_response_statuses=frozenset({200}),
)


async def fetch_post(post_id: str, *, headers: dict[str, str]) -> dict[str, Any] | None:
    url = API_URL.format(post_id=post_id)
    session = await HTTPClient.get_session()

    try:
        async with session.get(
            url, headers=headers, timeout=_RETRY_POLICY.request_timeout, middlewares=(_RETRY_POLICY,)
        ) as response:
            if response.status != 200:
                await logger.adebug("[Example] Post request failed", post_id=post_id, status=response.status)
                return None

            payload = dict_or_empty(orjson.loads(await response.read()))
            return payload or None
    except (TimeoutError, aiohttp.ClientError) as error:
        await logger.awarning("[Example] Post request error", post_id=post_id, error=str(error))
        return None
    except orjson.JSONDecodeError as error:
        await logger.adebug("[Example] Invalid post response", post_id=post_id, error=str(error))
        return None

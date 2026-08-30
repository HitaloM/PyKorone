from typing import TYPE_CHECKING, Any

import aiohttp
import orjson

from korone.http import RetryPolicy
from korone.logger import get_logger
from korone.modules.medias.download import DEFAULT_MEDIA_HEADERS, DEFAULT_MEDIA_TIMEOUT, TRANSIENT_MEDIA_STATUSES

logger = get_logger(__name__)

if TYPE_CHECKING:
    from korone.http import HttpClient


class TwitterClient:
    __slots__ = ("_http", "_retry")

    def __init__(self, http: HttpClient) -> None:
        self._http = http
        self._retry = RetryPolicy(
            attempts=3,
            timeout=DEFAULT_MEDIA_TIMEOUT,
            retryable_statuses=TRANSIENT_MEDIA_STATUSES,
            backoff_seconds=(0.8, 1.6),
            jitter_seconds=0.25,
            buffer_response_statuses=frozenset({200}),
        )

    async def fetch_json(self, url: str) -> dict[str, Any] | None:
        try:
            async with self._http.session.get(
                url, headers=DEFAULT_MEDIA_HEADERS, timeout=self._retry.request_timeout, middlewares=(self._retry,)
            ) as response:
                if response.status != 200:
                    await logger.adebug("[FXTwitter] Non-200 response", status=response.status, url=url)
                    return None
                data = orjson.loads(await response.read())
                if isinstance(data, dict):
                    return data
                await logger.adebug("[FXTwitter] Unexpected payload shape", payload_type=type(data).__name__, url=url)
        except (TimeoutError, aiohttp.ClientError) as error:
            await logger.awarning("[FXTwitter] Request error", error=str(error), url=url)
        except orjson.JSONDecodeError as error:
            await logger.adebug("[FXTwitter] JSON decode failed", error=str(error), url=url)
        return None

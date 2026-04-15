from __future__ import annotations

import asyncio
import random
from typing import Any

import aiohttp
import orjson

from korone.logger import get_logger
from korone.modules.medias.utils.provider_base import MediaProvider
from korone.utils.aiohttp_session import HTTPClient

logger = get_logger(__name__)

_RETRY_ATTEMPTS = 3
_RETRY_BASE_DELAY_SECONDS = 0.8
_RETRY_JITTER_SECONDS = 0.25


def _next_retry_delay(attempt: int) -> float:
    backoff = _RETRY_BASE_DELAY_SECONDS * (2 ** max(0, attempt - 1))
    return backoff + random.uniform(0.0, _RETRY_JITTER_SECONDS)


async def _sleep_before_retry(attempt: int) -> None:
    await asyncio.sleep(_next_retry_delay(attempt))


def _build_headers(extra_headers: dict[str, str] | None = None) -> dict[str, str]:
    headers = dict(MediaProvider._DEFAULT_HEADERS)
    if extra_headers:
        headers.update(extra_headers)
    return headers


async def _request_json(
    url: str,
    *,
    method: str = "GET",
    params: dict[str, str] | None = None,
    headers: dict[str, str] | None = None,
    log_label: str,
) -> dict[str, Any] | None:
    session = await HTTPClient.get_session()

    for attempt in range(1, _RETRY_ATTEMPTS + 1):
        try:
            async with session.request(
                method, url, params=params, headers=_build_headers(headers), timeout=MediaProvider._DEFAULT_TIMEOUT
            ) as response:
                if response.status != 200:
                    if attempt < _RETRY_ATTEMPTS and MediaProvider._should_retry_status(response.status):
                        await _sleep_before_retry(attempt)
                        continue

                    await logger.adebug(f"[{log_label}] Non-200 response", status=response.status, url=url)
                    return None

                payload = await response.read()
                data = orjson.loads(payload)
                if not isinstance(data, dict):
                    await logger.adebug(
                        f"[{log_label}] Unexpected payload shape", payload_type=type(data).__name__, url=url
                    )
                    return None

                return data
        except asyncio.CancelledError:
            raise
        except (TimeoutError, aiohttp.ClientError) as exc:
            if attempt < _RETRY_ATTEMPTS:
                await _sleep_before_retry(attempt)
                continue

            await logger.aerror(f"[{log_label}] Request error", error=str(exc), url=url)
            return None
        except orjson.JSONDecodeError as exc:
            await logger.adebug(f"[{log_label}] JSON decode failed", error=str(exc), url=url)
            return None

    return None


async def fetch_json(url: str) -> dict[str, Any] | None:
    return await _request_json(url, method="GET", log_label="FXTwitter")

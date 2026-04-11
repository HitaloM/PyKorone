from __future__ import annotations

import asyncio
import random
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

import aiohttp
import orjson

from korone.logger import get_logger
from korone.modules.medias.utils.provider_base import MediaProvider
from korone.utils.aiohttp_session import HTTPClient

from .constants import (
    TWITTER_API_BASE_HEADERS,
    TWITTER_GUEST_TOKEN_API,
    TWITTER_GUEST_TOKEN_TTL_SECONDS,
    TWITTER_STATUS_API,
    TWITTER_STATUS_FEATURES,
    TWITTER_STATUS_FIELD_TOGGLES,
    TWITTER_STATUS_VARIABLES,
)

if TYPE_CHECKING:
    from collections.abc import Mapping

logger = get_logger(__name__)

_RETRY_ATTEMPTS = 3
_RETRY_BASE_DELAY_SECONDS = 0.8
_RETRY_JITTER_SECONDS = 0.25


@dataclass(slots=True)
class _GuestTokenCache:
    token: str | None = None
    expires_at: float = 0.0


_GUEST_TOKEN_CACHE = _GuestTokenCache()
_GUEST_TOKEN_LOCK = asyncio.Lock()


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


def _json_query(value: Mapping[str, object]) -> str:
    return orjson.dumps(value).decode("utf-8")


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


async def fetch_guest_token() -> str | None:
    if _GUEST_TOKEN_CACHE.token and time.monotonic() < _GUEST_TOKEN_CACHE.expires_at:
        return _GUEST_TOKEN_CACHE.token

    async with _GUEST_TOKEN_LOCK:
        if _GUEST_TOKEN_CACHE.token and time.monotonic() < _GUEST_TOKEN_CACHE.expires_at:
            return _GUEST_TOKEN_CACHE.token

        payload = await _request_json(
            TWITTER_GUEST_TOKEN_API, method="POST", headers=TWITTER_API_BASE_HEADERS, log_label="Twitter API"
        )
        if not payload:
            return None

        guest_token = payload.get("guest_token")
        if not isinstance(guest_token, str) or not guest_token:
            await logger.adebug("[Twitter API] Missing guest token", payload_keys=list(payload.keys()))
            return None

        _GUEST_TOKEN_CACHE.token = guest_token
        _GUEST_TOKEN_CACHE.expires_at = time.monotonic() + TWITTER_GUEST_TOKEN_TTL_SECONDS
        return guest_token


async def fetch_twitter_tweet(status_id: str) -> dict[str, Any] | None:
    guest_token = await fetch_guest_token()
    if not guest_token:
        return None

    variables: dict[str, object] = dict(TWITTER_STATUS_VARIABLES)
    variables["tweetId"] = status_id

    headers = dict(TWITTER_API_BASE_HEADERS)
    headers["x-guest-token"] = guest_token
    headers["cookie"] = f"guest_id=v1:{guest_token};"

    params = {
        "variables": _json_query(variables),
        "features": _json_query(TWITTER_STATUS_FEATURES),
        "fieldToggles": _json_query(TWITTER_STATUS_FIELD_TOGGLES),
    }

    return await _request_json(
        TWITTER_STATUS_API, method="GET", params=params, headers=headers, log_label="Twitter API"
    )


async def fetch_json(url: str) -> dict[str, Any] | None:
    return await _request_json(url, method="GET", log_label="FXTwitter")

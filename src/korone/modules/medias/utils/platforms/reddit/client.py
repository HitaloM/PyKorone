import asyncio
import random
from typing import TYPE_CHECKING

import aiohttp

from korone.logger import get_logger
from korone.utils.aiohttp_session import HTTPClient

if TYPE_CHECKING:
    from collections.abc import Iterable

logger = get_logger(__name__)

_RETRY_ATTEMPTS = 3
_RETRY_BASE_DELAY_SECONDS = 0.35
_RETRY_JITTER_SECONDS = 0.2
_TRANSIENT_HTTP_STATUS: tuple[int, ...] = (408, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524, 525, 526)
_MAX_REDIRECTS = 5


def _next_retry_delay(attempt: int) -> float:
    backoff = _RETRY_BASE_DELAY_SECONDS * (2 ** max(0, attempt - 1))
    return backoff + random.uniform(0.0, _RETRY_JITTER_SECONDS)


async def _sleep_before_retry(attempt: int) -> None:
    await asyncio.sleep(_next_retry_delay(attempt))


def _is_transient_status(status: int, transient_statuses: Iterable[int]) -> bool:
    return status in transient_statuses


async def resolve_reddit_url(
    url: str, *, headers: dict[str, str], request_timeout: aiohttp.ClientTimeout
) -> str | None:
    try:
        session = await HTTPClient.get_session()
        async with session.get(
            url, headers=headers, allow_redirects=True, max_redirects=_MAX_REDIRECTS, timeout=request_timeout
        ) as response:
            resolved_url = str(response.url)
            return resolved_url if resolved_url != url else None
    except (TimeoutError, aiohttp.ClientError) as exc:
        await logger.awarning("[Reddit] Share URL resolution failed", error=str(exc), source_url=url)
        return None


async def request_redlib_page(
    url: str, *, headers: dict[str, str], cookies: dict[str, str], request_timeout: aiohttp.ClientTimeout
) -> dict[str, str] | None:
    response_payload = await _fetch_text_with_retry(
        url, headers=headers, cookies=cookies, request_timeout=request_timeout
    )
    if not response_payload:
        return None

    html_content, resolved_url = response_payload
    return {"html": html_content, "base_url": resolved_url}


async def fetch_text(
    url: str, *, headers: dict[str, str], cookies: dict[str, str], request_timeout: aiohttp.ClientTimeout
) -> str | None:
    response_payload = await _fetch_text_with_retry(
        url, headers=headers, cookies=cookies, request_timeout=request_timeout
    )
    if not response_payload:
        return None
    return response_payload[0]


async def _fetch_text_with_retry(
    url: str, *, headers: dict[str, str], cookies: dict[str, str], request_timeout: aiohttp.ClientTimeout
) -> tuple[str, str] | None:
    session = await HTTPClient.get_session()
    for attempt in range(1, _RETRY_ATTEMPTS + 1):
        try:
            async with session.get(
                url, headers=headers, cookies=cookies, allow_redirects=True, timeout=request_timeout
            ) as response:
                if response.status != 200:
                    if attempt < _RETRY_ATTEMPTS and _is_transient_status(response.status, _TRANSIENT_HTTP_STATUS):
                        await _sleep_before_retry(attempt)
                        continue
                    return None

                return await response.text(), str(response.url)
        except TimeoutError, aiohttp.ClientError:
            if attempt >= _RETRY_ATTEMPTS:
                raise
            await _sleep_before_retry(attempt)

    return None

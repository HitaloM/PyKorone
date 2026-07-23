import asyncio

import aiohttp

from korone.logger import get_logger
from korone.utils.aiohttp_session import HTTPClient

from .constants import (
    MAX_REDIRECTS,
    PIN_PAGE_URL,
    PINTEREST_TIMEOUT,
    REQUEST_RETRY_ATTEMPTS,
    REQUEST_RETRY_BASE_DELAY_SECONDS,
    URL_SHORTENER_REDIRECT_URL,
)

logger = get_logger(__name__)

_TRANSIENT_HTTP_STATUSES = {408, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524}


async def _sleep_before_retry(attempt: int) -> None:
    await asyncio.sleep(REQUEST_RETRY_BASE_DELAY_SECONDS * (2 ** max(0, attempt - 1)))


async def resolve_pin_url(url: str, *, headers: dict[str, str], short_id: str | None = None) -> str | None:
    request_url = URL_SHORTENER_REDIRECT_URL.format(short_id=short_id) if short_id else url
    session = await HTTPClient.get_session()

    for attempt in range(1, REQUEST_RETRY_ATTEMPTS + 1):
        try:
            async with session.get(
                request_url,
                headers=headers,
                timeout=PINTEREST_TIMEOUT,
                allow_redirects=True,
                max_redirects=MAX_REDIRECTS,
            ) as response:
                if response.status != 200:
                    if attempt < REQUEST_RETRY_ATTEMPTS and response.status in _TRANSIENT_HTTP_STATUSES:
                        await _sleep_before_retry(attempt)
                        continue

                    await logger.adebug(
                        "[Pinterest] Redirect resolution failed", status=response.status, source_url=url
                    )
                    return None

                return str(response.url)
        except (TimeoutError, aiohttp.ClientError) as error:
            if attempt < REQUEST_RETRY_ATTEMPTS:
                await _sleep_before_retry(attempt)
                continue

            await logger.awarning("[Pinterest] Redirect resolution error", error=str(error), source_url=url)
            return None

    return None


async def fetch_pin_page(post_id: str, *, headers: dict[str, str]) -> str | None:
    page_url = PIN_PAGE_URL.format(post_id=post_id)
    session = await HTTPClient.get_session()

    for attempt in range(1, REQUEST_RETRY_ATTEMPTS + 1):
        try:
            async with session.get(page_url, headers=headers, timeout=PINTEREST_TIMEOUT) as response:
                if response.status != 200:
                    if attempt < REQUEST_RETRY_ATTEMPTS and response.status in _TRANSIENT_HTTP_STATUSES:
                        await _sleep_before_retry(attempt)
                        continue

                    await logger.adebug("[Pinterest] Pin page request failed", status=response.status, post_id=post_id)
                    return None

                return await response.text()
        except (TimeoutError, aiohttp.ClientError, UnicodeDecodeError) as error:
            if attempt < REQUEST_RETRY_ATTEMPTS:
                await _sleep_before_retry(attempt)
                continue

            await logger.awarning("[Pinterest] Pin page request error", error=str(error), post_id=post_id)
            return None

    return None

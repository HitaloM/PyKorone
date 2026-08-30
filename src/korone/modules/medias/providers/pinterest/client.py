from typing import TYPE_CHECKING

import aiohttp

from korone.http import RetryPolicy
from korone.logger import get_logger

from .constants import (
    MAX_REDIRECTS,
    PIN_PAGE_URL,
    PINTEREST_TIMEOUT,
    REQUEST_RETRY_ATTEMPTS,
    REQUEST_RETRY_BASE_DELAY_SECONDS,
    URL_SHORTENER_REDIRECT_URL,
)

logger = get_logger(__name__)

if TYPE_CHECKING:
    from korone.http import HttpClient


class PinterestClient:
    __slots__ = ("_http", "_page_retry", "_redirect_retry")

    def __init__(self, http: HttpClient) -> None:
        self._http = http
        statuses = frozenset({408, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524})
        backoff = tuple(
            REQUEST_RETRY_BASE_DELAY_SECONDS * (2**attempt) for attempt in range(REQUEST_RETRY_ATTEMPTS - 1)
        )
        self._redirect_retry = RetryPolicy(
            attempts=REQUEST_RETRY_ATTEMPTS,
            timeout=PINTEREST_TIMEOUT,
            retryable_statuses=statuses,
            backoff_seconds=backoff,
        )
        self._page_retry = RetryPolicy(
            attempts=REQUEST_RETRY_ATTEMPTS,
            timeout=PINTEREST_TIMEOUT,
            retryable_statuses=statuses,
            backoff_seconds=backoff,
            buffer_response_statuses=frozenset({200}),
        )

    async def resolve_pin_url(self, url: str, *, headers: dict[str, str], short_id: str | None = None) -> str | None:
        request_url = URL_SHORTENER_REDIRECT_URL.format(short_id=short_id) if short_id else url
        try:
            async with self._http.session.get(
                request_url,
                headers=headers,
                timeout=self._redirect_retry.request_timeout,
                allow_redirects=True,
                max_redirects=MAX_REDIRECTS,
                middlewares=(self._redirect_retry,),
            ) as response:
                if response.status == 200:
                    return str(response.url)
                await logger.adebug("[Pinterest] Redirect resolution failed", status=response.status, source_url=url)
        except (TimeoutError, aiohttp.ClientError) as error:
            await logger.awarning("[Pinterest] Redirect resolution error", error=str(error), source_url=url)
        return None

    async def fetch_pin_page(self, post_id: str, *, headers: dict[str, str]) -> str | None:
        try:
            async with self._http.session.get(
                PIN_PAGE_URL.format(post_id=post_id),
                headers=headers,
                timeout=self._page_retry.request_timeout,
                middlewares=(self._page_retry,),
            ) as response:
                if response.status == 200:
                    return await response.text()
                await logger.adebug("[Pinterest] Pin page request failed", status=response.status, post_id=post_id)
        except (TimeoutError, aiohttp.ClientError, UnicodeDecodeError) as error:
            await logger.awarning("[Pinterest] Pin page request error", error=str(error), post_id=post_id)
        return None

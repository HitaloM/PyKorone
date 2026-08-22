import aiohttp

from korone.logger import get_logger
from korone.utils.aiohttp_session import HTTPClient, RetryPolicy

from .constants import (
    MAX_REDIRECTS,
    PIN_PAGE_URL,
    PINTEREST_TIMEOUT,
    REQUEST_RETRY_ATTEMPTS,
    REQUEST_RETRY_BASE_DELAY_SECONDS,
    URL_SHORTENER_REDIRECT_URL,
)

logger = get_logger(__name__)

_TRANSIENT_HTTP_STATUSES = frozenset({408, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524})
_RETRY_BACKOFF = tuple(REQUEST_RETRY_BASE_DELAY_SECONDS * (2**attempt) for attempt in range(REQUEST_RETRY_ATTEMPTS - 1))
_REDIRECT_RETRY_POLICY = RetryPolicy(
    attempts=REQUEST_RETRY_ATTEMPTS,
    timeout=PINTEREST_TIMEOUT,
    retryable_statuses=_TRANSIENT_HTTP_STATUSES,
    backoff_seconds=_RETRY_BACKOFF,
)
_PAGE_RETRY_POLICY = RetryPolicy(
    attempts=REQUEST_RETRY_ATTEMPTS,
    timeout=PINTEREST_TIMEOUT,
    retryable_statuses=_TRANSIENT_HTTP_STATUSES,
    backoff_seconds=_RETRY_BACKOFF,
    buffer_response_statuses=frozenset({200}),
)


async def resolve_pin_url(url: str, *, headers: dict[str, str], short_id: str | None = None) -> str | None:
    request_url = URL_SHORTENER_REDIRECT_URL.format(short_id=short_id) if short_id else url
    session = await HTTPClient.get_session()

    try:
        async with session.get(
            request_url,
            headers=headers,
            timeout=_REDIRECT_RETRY_POLICY.request_timeout,
            allow_redirects=True,
            max_redirects=MAX_REDIRECTS,
            middlewares=(_REDIRECT_RETRY_POLICY,),
        ) as response:
            if response.status != 200:
                await logger.adebug("[Pinterest] Redirect resolution failed", status=response.status, source_url=url)
                return None

            return str(response.url)
    except (TimeoutError, aiohttp.ClientError) as error:
        await logger.awarning("[Pinterest] Redirect resolution error", error=str(error), source_url=url)
        return None


async def fetch_pin_page(post_id: str, *, headers: dict[str, str]) -> str | None:
    page_url = PIN_PAGE_URL.format(post_id=post_id)
    session = await HTTPClient.get_session()

    try:
        async with session.get(
            page_url, headers=headers, timeout=_PAGE_RETRY_POLICY.request_timeout, middlewares=(_PAGE_RETRY_POLICY,)
        ) as response:
            if response.status != 200:
                await logger.adebug("[Pinterest] Pin page request failed", status=response.status, post_id=post_id)
                return None

            return await response.text()
    except (TimeoutError, aiohttp.ClientError, UnicodeDecodeError) as error:
        await logger.awarning("[Pinterest] Pin page request error", error=str(error), post_id=post_id)
        return None

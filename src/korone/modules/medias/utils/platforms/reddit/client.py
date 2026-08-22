import aiohttp

from korone.logger import get_logger
from korone.utils.aiohttp_session import HTTPClient, RetryPolicy

logger = get_logger(__name__)

_RETRY_ATTEMPTS = 3
_RETRY_BASE_DELAY_SECONDS = 0.35
_RETRY_JITTER_SECONDS = 0.2
_TRANSIENT_HTTP_STATUS = frozenset({408, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524, 525, 526})
_MAX_REDIRECTS = 5


def _text_retry_policy(request_timeout: aiohttp.ClientTimeout) -> RetryPolicy:
    return RetryPolicy(
        attempts=_RETRY_ATTEMPTS,
        timeout=request_timeout,
        retryable_statuses=_TRANSIENT_HTTP_STATUS,
        backoff_seconds=(_RETRY_BASE_DELAY_SECONDS, _RETRY_BASE_DELAY_SECONDS * 2),
        jitter_seconds=_RETRY_JITTER_SECONDS,
        buffer_response_statuses=frozenset({200}),
    )


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
    retry_policy = _text_retry_policy(request_timeout)
    async with session.get(
        url,
        headers=headers,
        cookies=cookies,
        allow_redirects=True,
        timeout=retry_policy.request_timeout,
        middlewares=(retry_policy,),
    ) as response:
        if response.status != 200:
            return None

        return await response.text(), str(response.url)

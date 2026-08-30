from typing import TYPE_CHECKING

import aiohttp

from korone.http import RetryPolicy
from korone.logger import get_logger

from . import anubis

logger = get_logger(__name__)

if TYPE_CHECKING:
    from korone.http import HttpClient


class RedditClient:
    __slots__ = ("_http",)

    _TRANSIENT_STATUSES = frozenset({408, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524, 525, 526})
    _MAX_REDIRECTS = 5

    def __init__(self, http: HttpClient) -> None:
        self._http = http

    async def resolve_url(
        self, url: str, *, headers: dict[str, str], request_timeout: aiohttp.ClientTimeout
    ) -> str | None:
        try:
            async with self._http.session.get(
                url, headers=headers, allow_redirects=True, max_redirects=self._MAX_REDIRECTS, timeout=request_timeout
            ) as response:
                resolved_url = str(response.url)
                return resolved_url if resolved_url != url else None
        except (TimeoutError, aiohttp.ClientError) as error:
            await logger.awarning("[Reddit] Share URL resolution failed", error=str(error), source_url=url)
            return None

    async def request_page(
        self, url: str, *, headers: dict[str, str], cookies: dict[str, str], request_timeout: aiohttp.ClientTimeout
    ) -> dict[str, str] | None:
        payload = await self._fetch_text_with_retry(
            url, headers=headers, cookies=cookies, request_timeout=request_timeout
        )
        return {"html": payload[0], "base_url": payload[1]} if payload else None

    async def fetch_text(
        self, url: str, *, headers: dict[str, str], cookies: dict[str, str], request_timeout: aiohttp.ClientTimeout
    ) -> str | None:
        payload = await self._fetch_text_with_retry(
            url, headers=headers, cookies=cookies, request_timeout=request_timeout
        )
        return payload[0] if payload else None

    async def solve_anubis(
        self,
        *,
        challenge_html: str,
        challenge_url: str,
        headers: dict[str, str],
        request_timeout: aiohttp.ClientTimeout,
    ) -> dict[str, str] | None:
        return await anubis.solve_challenge(
            self._http.session,
            challenge_html=challenge_html,
            challenge_url=challenge_url,
            headers=headers,
            request_timeout=request_timeout,
        )

    async def _fetch_text_with_retry(
        self, url: str, *, headers: dict[str, str], cookies: dict[str, str], request_timeout: aiohttp.ClientTimeout
    ) -> tuple[str, str] | None:
        retry = RetryPolicy(
            attempts=3,
            timeout=request_timeout,
            retryable_statuses=self._TRANSIENT_STATUSES,
            backoff_seconds=(0.35, 0.7),
            jitter_seconds=0.2,
            buffer_response_statuses=frozenset({200}),
        )
        async with self._http.session.get(
            url,
            headers=headers,
            cookies=cookies,
            allow_redirects=True,
            timeout=retry.request_timeout,
            middlewares=(retry,),
        ) as response:
            if response.status != 200:
                return None
            return await response.text(), str(response.url)

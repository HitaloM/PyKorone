import asyncio
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from time import monotonic
from typing import TYPE_CHECKING
from urllib.parse import urljoin

import aiohttp

from korone.logger import get_logger

from . import anubis, parser
from .constants import BLOCK_MARKERS, REDLIB_REQUEST_COOKIES
from .models import _PageResponse

logger = get_logger(__name__)

if TYPE_CHECKING:
    from korone.http import HttpClient


class RedditClient:
    __slots__ = ("_challenge_slot", "_http")

    _TRANSIENT_STATUSES = frozenset({408, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524, 525, 526})
    _MAX_REDIRECTS = 5
    _MAX_CHALLENGE_STEPS = 3

    def __init__(self, http: HttpClient) -> None:
        self._http = http
        self._challenge_slot = asyncio.Semaphore(1)

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
            await logger.adebug("[Reddit] Share URL resolution failed", error=str(error), source_url=url)
            return None

    async def request_page(
        self, url: str, *, headers: dict[str, str], cookies: dict[str, str], request_timeout: aiohttp.ClientTimeout
    ) -> _PageResponse | None:
        async with asyncio.timeout(request_timeout.total):
            page = await self._fetch_text_with_retry(
                url, headers=headers, cookies=cookies, request_timeout=request_timeout
            )
            for _step in range(self._MAX_CHALLENGE_STEPS):
                if not parser.looks_like_block_page(page.body, BLOCK_MARKERS):
                    return page
                refresh = parser.extract_go_away_refresh(page.body, page.url)
                if refresh is not None:
                    delay, target = refresh
                    await asyncio.sleep(delay)
                    page = await self._request_once(
                        target, headers=headers, cookies=cookies, request_timeout=request_timeout, same_origin_only=True
                    )
                else:
                    info = anubis.extract_challenge_info(page.body, page.url)
                    if info is None:
                        await logger.adebug("[Reddit] Unrecognized challenge", url=page.url, status=page.status)
                        return None
                    if not parser.same_origin(page.url, info.pass_url):
                        await logger.adebug("[Reddit] Invalid challenge origin", url=page.url)
                        return None
                    async with self._challenge_slot:
                        params = await anubis.solve_challenge_parameters(info, page.url)
                    if params is None:
                        return None
                    page = await self._request_once(
                        info.pass_url,
                        headers=headers,
                        cookies=REDLIB_REQUEST_COOKIES,
                        request_timeout=request_timeout,
                        params=params,
                        same_origin_only=True,
                    )
                if page.status != 200 and not parser.looks_like_block_page(page.body, BLOCK_MARKERS):
                    return page
            if parser.looks_like_block_page(page.body, BLOCK_MARKERS):
                await logger.adebug("[Reddit] Challenge step limit reached", url=page.url, status=page.status)
                return None
            return page

    async def fetch_text(
        self, url: str, *, headers: dict[str, str], cookies: dict[str, str], request_timeout: aiohttp.ClientTimeout
    ) -> str | None:
        async with asyncio.timeout(request_timeout.total):
            page = await self._fetch_text_with_retry(
                url, headers=headers, cookies=cookies, request_timeout=request_timeout
            )
        return page.body if page.status == 200 else None

    async def _fetch_text_with_retry(
        self, url: str, *, headers: dict[str, str], cookies: dict[str, str], request_timeout: aiohttp.ClientTimeout
    ) -> _PageResponse:
        deadline = monotonic() + request_timeout.total if request_timeout.total is not None else None
        for attempt in range(3):
            try:
                page = await self._request_once(url, headers=headers, cookies=cookies, request_timeout=request_timeout)
            except TimeoutError, aiohttp.ClientError:
                if attempt == 2:
                    raise
                await asyncio.sleep(0.35 * (2**attempt))
                continue
            # Inspect the body before retrying: Anubis and go-away also use 429/418.
            if parser.looks_like_block_page(page.body, BLOCK_MARKERS):
                return page
            if page.status not in self._TRANSIENT_STATUSES or attempt == 2:
                return page
            delay = 0.35 * (2**attempt)
            if page.status == 429:
                retry_after = self._retry_after_seconds(page.retry_after)
                if retry_after is None:
                    return page
                delay = max(delay, retry_after)
            if deadline is not None and monotonic() + delay >= deadline:
                return page
            await asyncio.sleep(delay)
        raise AssertionError

    async def _request_once(
        self,
        url: str,
        *,
        headers: dict[str, str],
        cookies: dict[str, str],
        request_timeout: aiohttp.ClientTimeout,
        params: dict[str, str] | None = None,
        same_origin_only: bool = False,
    ) -> _PageResponse:
        origin = url
        redirects: list[tuple[int, str]] = []
        for redirect in range(self._MAX_REDIRECTS + 1):
            async with self._http.session.get(
                url, headers=headers, cookies=cookies, params=params, allow_redirects=False, timeout=request_timeout
            ) as response:
                page = _PageResponse(
                    status=response.status,
                    url=str(response.url),
                    body=await response.text(),
                    redirects=tuple(redirects),
                    retry_after=response.headers.get("Retry-After"),
                )
                location = response.headers.get("Location")
                if response.status not in {301, 302, 303, 307, 308} or not location:
                    return page
                target = urljoin(page.url, location)
                if same_origin_only and not parser.same_origin(origin, target):
                    return page
                if redirect == self._MAX_REDIRECTS:
                    return page
                redirects.append((page.status, page.url))
                url, params = target, None
        raise AssertionError

    @staticmethod
    def _retry_after_seconds(value: str | None) -> float | None:
        if value is None:
            return None
        try:
            return max(0.0, float(int(value)))
        except ValueError:
            try:
                date = parsedate_to_datetime(value)
                if date.tzinfo is None:
                    date = date.replace(tzinfo=UTC)
                return max(0.0, (date - datetime.now(UTC)).total_seconds())
            except ValueError, TypeError, OverflowError:
                return None

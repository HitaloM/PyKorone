import asyncio
import math
import random
from contextlib import asynccontextmanager
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import TYPE_CHECKING, Final

from aiohttp import (
    ClientError,
    ClientHandlerType,
    ClientRequest,
    ClientResponse,
    ClientSession,
    ClientTimeout,
    TCPConnector,
)

from korone.logger import get_logger

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator

logger = get_logger(__name__)

_IDEMPOTENT_METHODS: Final[frozenset[str]] = frozenset({"DELETE", "GET", "HEAD", "OPTIONS", "PUT", "TRACE"})


@dataclass(frozen=True, slots=True, kw_only=True)
class RetryPolicy:
    attempts: int
    timeout: ClientTimeout
    retryable_statuses: frozenset[int] = frozenset()
    backoff_seconds: tuple[float, ...] = ()
    jitter_seconds: float = 0.0
    retry_timeouts: bool = True
    retry_client_errors: bool = True
    respect_retry_after: bool = False
    max_retry_after_seconds: float | None = None
    methods: frozenset[str] = _IDEMPOTENT_METHODS
    buffer_response_statuses: frozenset[int] = frozenset()

    def __post_init__(self) -> None:
        if self.attempts < 1:
            msg = "Retry attempts must be at least one"
            raise ValueError(msg)
        if len(self.backoff_seconds) != self.attempts - 1:
            msg = "Retry backoff must contain one delay for each possible retry"
            raise ValueError(msg)
        if any(delay < 0 for delay in self.backoff_seconds):
            msg = "Retry backoff delays cannot be negative"
            raise ValueError(msg)
        if self.jitter_seconds < 0:
            msg = "Retry jitter cannot be negative"
            raise ValueError(msg)
        if self.max_retry_after_seconds is not None and self.max_retry_after_seconds < 0:
            msg = "Maximum Retry-After delay cannot be negative"
            raise ValueError(msg)
        if any(method != method.upper() for method in self.methods):
            msg = "Retry methods must be uppercase"
            raise ValueError(msg)

    @property
    def request_timeout(self) -> ClientTimeout:
        if self.timeout.total is None:
            return self.timeout
        return ClientTimeout(
            total=None,
            connect=self.timeout.connect,
            sock_read=self.timeout.sock_read,
            sock_connect=self.timeout.sock_connect,
            ceil_threshold=self.timeout.ceil_threshold,
        )

    @asynccontextmanager
    async def _attempt_timeout(self) -> AsyncGenerator[None]:
        total = self.timeout.total
        if total is None or total <= 0:
            yield
            return

        loop = asyncio.get_running_loop()
        deadline = loop.time() + total
        if total >= self.timeout.ceil_threshold:
            deadline = math.ceil(deadline)
        async with asyncio.timeout_at(deadline):
            yield

    def _retry_delay(self, response: ClientResponse | None, attempt: int) -> float:
        delay = self.backoff_seconds[attempt - 1]
        if self.jitter_seconds:
            delay += random.uniform(0.0, self.jitter_seconds)
        if response is not None and self.respect_retry_after:
            delay = max(delay, self._parse_retry_after(response))
        return delay

    def _parse_retry_after(self, response: ClientResponse) -> float:
        value = response.headers.get("Retry-After", "").strip()
        if not value:
            return 0.0

        try:
            retry_after = max(0.0, float(value))
        except ValueError:
            try:
                retry_at = parsedate_to_datetime(value)
            except TypeError, ValueError, OverflowError:
                return 0.0
            if retry_at.tzinfo is None:
                retry_at = retry_at.replace(tzinfo=UTC)
            retry_after = max(0.0, (retry_at - datetime.now(UTC)).total_seconds())

        if self.max_retry_after_seconds is not None:
            return min(retry_after, self.max_retry_after_seconds)
        return retry_after

    async def __call__(self, request: ClientRequest, handler: ClientHandlerType) -> ClientResponse:
        retry_allowed = request.method.upper() in self.methods
        attempts = self.attempts if retry_allowed else 1

        for attempt in range(1, attempts + 1):
            response: ClientResponse | None = None
            retry_status: int | None = None
            retry_error_type: str | None = None
            try:
                async with self._attempt_timeout():
                    response = await handler(request)
                    if response.status in self.retryable_statuses and attempt < attempts:
                        retry_status = response.status
                    else:
                        if response.status in self.buffer_response_statuses:
                            await response.read()
                        return response
            except asyncio.CancelledError:
                if response is not None:
                    response.close()
                raise
            except TimeoutError as error:
                if response is not None:
                    response.close()
                    response = None
                if not self.retry_timeouts or attempt >= attempts:
                    raise
                retry_error_type = type(error).__name__
            except ClientError as error:
                if response is not None:
                    response.close()
                    response = None
                if not self.retry_client_errors or attempt >= attempts:
                    raise
                retry_error_type = type(error).__name__
            except BaseException:
                if response is not None:
                    response.close()
                raise

            delay = self._retry_delay(response, attempt)
            if response is not None:
                response.release()
                await response.wait_for_close()

            await logger.adebug(
                "[HTTP] Retrying request",
                method=request.method,
                target_host=request.url.host,
                target_path=request.url.path,
                attempt=attempt,
                attempts=attempts,
                status=retry_status,
                error_type=retry_error_type,
                retry_after_seconds=delay,
            )
            await asyncio.sleep(delay)

        msg = "HTTP retry loop exhausted without returning or raising"
        raise RuntimeError(msg)


class HTTPClient:
    _session: ClientSession | None = None
    _connector: TCPConnector | None = None

    @classmethod
    async def get_session(cls) -> ClientSession:
        if cls._session is None or cls._session.closed:
            if cls._connector is None or cls._connector.closed:
                cls._connector = TCPConnector(
                    use_dns_cache=True,
                    limit=100,
                    limit_per_host=30,
                    ttl_dns_cache=300,
                    keepalive_timeout=30,
                    enable_cleanup_closed=True,
                    force_close=False,
                )
            cls._session = ClientSession(connector=cls._connector)
        return cls._session

    @classmethod
    async def close(cls) -> None:
        if cls._session and not cls._session.closed:
            await cls._session.close()
            cls._session = None

        if cls._connector and not cls._connector.closed:
            await cls._connector.close()
            cls._connector = None

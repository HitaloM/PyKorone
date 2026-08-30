import asyncio
import contextlib
import mimetypes
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal
from urllib.parse import urlparse

import aiofiles
import aiofiles.os
import aiohttp
from aiogram.types import BufferedInputFile

from korone.constants import TELEGRAM_MEDIA_MAX_FILE_SIZE_BYTES
from korone.logger import get_logger

from .models import MediaKind, MediaSource, PreparedMedia

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Awaitable, Callable, Sequence

    from aiogram.types import InputFile

    from korone.http import HttpClient

    from .cache import MediaCache

DEFAULT_MEDIA_HEADERS: Final[dict[str, str]] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en;q=0.8,en-US;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
}
DEFAULT_MEDIA_TIMEOUT: Final[aiohttp.ClientTimeout] = aiohttp.ClientTimeout(total=60)
TRANSIENT_MEDIA_STATUSES: Final[frozenset[int]] = frozenset({408, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524})

logger = get_logger(__name__)


async def _noop_cleanup() -> None:
    pass


@dataclass(frozen=True, slots=True, kw_only=True)
class DownloadOptions:
    filename_prefix: str
    label: str
    max_size: int | None = TELEGRAM_MEDIA_MAX_FILE_SIZE_BYTES
    headers: dict[str, str] = field(default_factory=lambda: dict(DEFAULT_MEDIA_HEADERS))
    timeout: aiohttp.ClientTimeout = DEFAULT_MEDIA_TIMEOUT


@dataclass(frozen=True, slots=True)
class DownloadRequest:
    source: MediaSource
    index: int
    options: DownloadOptions


@dataclass(frozen=True, slots=True)
class _DownloadContext:
    max_size: int | None
    log: dict[str, object]


type SourceLoader = Callable[[DownloadRequest], Awaitable[PreparedMedia | None]]


class MediaDownloader:
    __slots__ = ("_cache", "_http", "_slots")

    _RETRY_ATTEMPTS = 3
    _RETRY_BASE_DELAY_SECONDS = 0.35
    _RETRY_JITTER_SECONDS = 0.2
    _CHUNK_SIZE_BYTES = 64 * 1024

    def __init__(self, http: HttpClient, cache: MediaCache, slots: asyncio.Semaphore) -> None:
        self._http = http
        self._cache = cache
        self._slots = slots

    async def download(
        self, sources: Sequence[MediaSource], *, options: DownloadOptions, loader: SourceLoader | None = None
    ) -> tuple[PreparedMedia, ...]:
        if not sources:
            return ()

        requests = tuple(
            DownloadRequest(source=source, index=index, options=options)
            for index, source in enumerate(sources, start=1)
        )
        results: list[PreparedMedia | None] = [None] * len(requests)
        cached_file_ids = await self._cache.get_source_file_ids([request.source.url for request in requests])
        pending: list[DownloadRequest] = []
        for request, file_id in zip(requests, cached_file_ids, strict=True):
            if file_id:
                results[request.index - 1] = self._cached_media(request, file_id)
            else:
                pending.append(request)

        source_loader = loader or self.download_source
        async with asyncio.TaskGroup() as task_group:
            for request in pending:
                task_group.create_task(
                    self._download_worker(request, source_loader, results),
                    name=f"media-download:{options.label}:{request.index}",
                )

        await logger.adebug(
            "[Medias] Download batch finished",
            provider=options.label,
            source_count=len(requests),
            source_cache_hits=len(requests) - len(pending),
            downloaded_count=sum(isinstance(item.file, BufferedInputFile) for item in results if item is not None),
        )
        return tuple(item for item in results if item is not None)

    async def get_cached_media(self, request: DownloadRequest) -> PreparedMedia | None:
        file_ids = await self._cache.get_source_file_ids((request.source.url,))
        return self._cached_media(request, file_ids[0]) if file_ids and file_ids[0] else None

    @contextlib.asynccontextmanager
    async def reserve_slot(self) -> AsyncIterator[None]:
        async with self._slots:
            yield

    async def _download_worker(
        self, request: DownloadRequest, loader: SourceLoader, results: list[PreparedMedia | None]
    ) -> None:
        try:
            results[request.index - 1] = await loader(request)
        except asyncio.CancelledError:
            raise
        except TimeoutError:
            await logger.awarning("[Medias] Download source timed out", **self._request_log(request))
        except Exception:  # ruff: ignore[blind-except]
            await logger.aexception("[Medias] Download worker failed", **self._request_log(request))

    async def download_source(self, request: DownloadRequest) -> PreparedMedia | None:
        source = request.source
        payload_result = await self.fetch_payload(
            source.url, request, stage="source", max_size=request.options.max_size
        )
        if payload_result is None:
            return None

        payload, content_type = payload_result
        extension = self.guess_extension(source.url, content_type, source.kind)
        thumbnail: InputFile | None = None
        if source.thumbnail_url and source.kind == MediaKind.VIDEO:
            thumbnail = await self.download_thumbnail(source.thumbnail_url, request)

        filename = f"{request.options.filename_prefix}_{request.index}{extension}"
        return PreparedMedia(
            kind=source.kind,
            file=BufferedInputFile(payload, filename),
            filename=filename,
            source_url=source.url,
            thumbnail=thumbnail,
            duration=source.duration,
            width=source.width,
            height=source.height,
        )

    async def fetch_payload(
        self, url: str, request: DownloadRequest, *, stage: Literal["source", "thumbnail"], max_size: int | None = None
    ) -> tuple[bytes, str] | None:
        async def consume(response: aiohttp.ClientResponse) -> tuple[bytes, str] | None:
            payload = await self._read_payload(response, max_size=max_size)
            return (payload, response.headers.get("Content-Type", "")) if payload is not None else None

        return await self._fetch_with_retry(url, request, stage=stage, max_size=max_size, consume=consume)

    async def fetch_to_path(
        self, url: str, request: DownloadRequest, destination: Path, *, max_size: int | None
    ) -> int | None:
        async def cleanup() -> None:
            await self._remove_path(destination)

        async def consume(response: aiohttp.ClientResponse) -> int | None:
            return await self._write_response_to_path(response, destination, max_size=max_size)

        return await self._fetch_with_retry(
            url, request, stage="source", max_size=max_size, consume=consume, cleanup=cleanup
        )

    async def download_thumbnail(self, url: str, request: DownloadRequest) -> InputFile | None:
        payload_result = await self.fetch_payload(url, request, stage="thumbnail")
        if payload_result is None:
            return None
        payload, content_type = payload_result
        extension = self.guess_extension(url, content_type, MediaKind.PHOTO)
        return BufferedInputFile(payload, f"{request.options.filename_prefix}_{request.index}_thumb{extension}")

    async def _fetch_with_retry[Result](
        self,
        url: str,
        request: DownloadRequest,
        *,
        stage: Literal["source", "thumbnail"],
        max_size: int | None,
        consume: Callable[[aiohttp.ClientResponse], Awaitable[Result | None]],
        cleanup: Callable[[], Awaitable[None]] | None = None,
    ) -> Result | None:
        cleanup_callback = cleanup or _noop_cleanup
        context = _DownloadContext(
            max_size=max_size, log={**self._request_log(request), "source_url": url, "stage": stage}
        )
        for attempt in range(1, self._RETRY_ATTEMPTS + 1):
            await cleanup_callback()
            try:
                async with (
                    self._slots,
                    self._http.session.get(
                        url, headers=request.options.headers, timeout=request.options.timeout
                    ) as response,
                ):
                    should_retry, result = await self._consume_response(
                        response, attempt=attempt, consume=consume, cleanup=cleanup_callback, context=context
                    )
                    if not should_retry:
                        return result
                await self._sleep_before_retry(attempt)
            except asyncio.CancelledError:
                await cleanup_callback()
                raise
            except (TimeoutError, aiohttp.ClientError) as error:
                if await self._recover_network_error(
                    error, attempt=attempt, cleanup=cleanup_callback, log_context=context.log
                ):
                    continue
                return None
            except OSError as error:
                await cleanup_callback()
                await logger.awarning(
                    "[Medias] Download file error", **context.log, error_type=type(error).__name__, error=str(error)
                )
                return None
            except Exception:  # ruff: ignore[blind-except]
                await cleanup_callback()
                await logger.aexception("[Medias] Download unexpected error", **context.log)
                return None
        return None

    async def _consume_response[Result](
        self,
        response: aiohttp.ClientResponse,
        *,
        attempt: int,
        consume: Callable[[aiohttp.ClientResponse], Awaitable[Result | None]],
        cleanup: Callable[[], Awaitable[None]],
        context: _DownloadContext,
    ) -> tuple[bool, Result | None]:
        if response.status != 200:
            if attempt < self._RETRY_ATTEMPTS and response.status in TRANSIENT_MEDIA_STATUSES:
                return True, None
            await logger.adebug("[Medias] Download rejected by upstream", **context.log, status=response.status)
            return False, None

        if context.max_size and (content_len := response.content_length) and content_len > context.max_size:
            await logger.adebug("[Medias] Download exceeded size limit", **context.log, size=content_len)
            return False, None

        result = await consume(response)
        if result is not None:
            return False, result
        await cleanup()
        await logger.adebug(
            "[Medias] Download exceeded size limit while streaming", **context.log, max_size=context.max_size
        )
        return False, None

    async def _recover_network_error(
        self,
        error: TimeoutError | aiohttp.ClientError,
        *,
        attempt: int,
        cleanup: Callable[[], Awaitable[None]],
        log_context: dict[str, object],
    ) -> bool:
        await cleanup()
        if attempt < self._RETRY_ATTEMPTS:
            await self._sleep_before_retry(attempt)
            return True

        if isinstance(error, TimeoutError):
            await logger.awarning("[Medias] Download timed out", **log_context, attempts=attempt)
        elif isinstance(error, aiohttp.ClientPayloadError):
            await logger.awarning("[Medias] Download payload truncated", **log_context, attempts=attempt)
        else:
            await logger.awarning(
                "[Medias] Download network error",
                **log_context,
                attempts=attempt,
                error_type=type(error).__name__,
                error=str(error),
            )
        return False

    async def _sleep_before_retry(self, attempt: int) -> None:
        backoff = self._RETRY_BASE_DELAY_SECONDS * (2 ** max(0, attempt - 1))
        await asyncio.sleep(backoff + random.uniform(0.0, self._RETRY_JITTER_SECONDS))

    async def _read_payload(self, response: aiohttp.ClientResponse, *, max_size: int | None) -> bytes | None:
        if max_size is None:
            return await response.read()
        payload = bytearray()
        async for chunk in response.content.iter_chunked(self._CHUNK_SIZE_BYTES):
            if not chunk:
                continue
            if len(payload) + len(chunk) > max_size:
                return None
            payload.extend(chunk)
        return bytes(payload)

    async def _write_response_to_path(
        self, response: aiohttp.ClientResponse, destination: Path, *, max_size: int | None
    ) -> int | None:
        total_size = 0
        async with aiofiles.open(destination, "wb") as output_file:
            async for chunk in response.content.iter_chunked(self._CHUNK_SIZE_BYTES):
                if not chunk:
                    continue
                total_size += len(chunk)
                if max_size is not None and total_size > max_size:
                    return None
                await output_file.write(chunk)
        return total_size

    @staticmethod
    async def _remove_path(path: Path) -> None:
        with contextlib.suppress(FileNotFoundError):
            await aiofiles.os.remove(path)

    @staticmethod
    def _cached_media(request: DownloadRequest, file_id: str) -> PreparedMedia:
        source = request.source
        return PreparedMedia(
            kind=source.kind,
            file=file_id,
            filename=f"{request.options.filename_prefix}_{request.index}",
            source_url=source.url,
            duration=source.duration,
            width=source.width,
            height=source.height,
        )

    @staticmethod
    def _request_log(request: DownloadRequest) -> dict[str, object]:
        return {
            "provider": request.options.label,
            "source_url": request.source.url,
            "source_index": request.index,
            "source_kind": request.source.kind.value,
        }

    @staticmethod
    def guess_extension(url: str, content_type: str, kind: MediaKind) -> str:
        path = Path(urlparse(url).path)
        if path.suffix:
            return path.suffix
        if content_type:
            extension = mimetypes.guess_extension(content_type.split(";", maxsplit=1)[0].strip())
            if extension:
                return ".jpg" if extension == ".jpe" else extension
        return ".mp4" if kind == MediaKind.VIDEO else ".jpg"

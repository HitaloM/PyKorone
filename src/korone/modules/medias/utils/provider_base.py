import asyncio
import contextlib
import mimetypes
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Literal
from urllib.parse import urlparse

import aiofiles
import aiofiles.os
import aiohttp
from aiogram.types import BufferedInputFile

from korone.constants import TELEGRAM_MEDIA_MAX_FILE_SIZE_BYTES
from korone.logger import get_logger
from korone.modules.utils_.file_id_cache import get_cached_file_payload, get_cached_file_payloads
from korone.utils.aiohttp_session import HTTPClient

from .cache import media_source_cache_key
from .resources import MEDIA_DOWNLOAD_SLOTS
from .types import MediaItem, MediaKind, MediaSource

if TYPE_CHECKING:
    import re
    from collections.abc import Sequence

    from aiogram.types import InputFile

    from .types import MediaPost

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class MediaDownloadRequest:
    source: MediaSource
    index: int
    filename_prefix: str
    max_size: int | None
    label: str


class MediaProvider(ABC):
    name: ClassVar[str]
    website: ClassVar[str]
    pattern: ClassVar[re.Pattern[str]]
    author_handle_prefix: ClassVar[str] = "@"
    show_author_name: ClassVar[bool] = True

    _DEFAULT_HEADERS: ClassVar[dict[str, str]] = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/145.0.0.0 Safari/537.36 Edg/145.0.0.0"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en;q=0.8,en-US;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
    }
    _DEFAULT_TIMEOUT: ClassVar[aiohttp.ClientTimeout] = aiohttp.ClientTimeout(total=60)
    _DOWNLOAD_RETRY_ATTEMPTS: ClassVar[int] = 3
    _DOWNLOAD_RETRY_BASE_DELAY_SECONDS: ClassVar[float] = 0.35
    _DOWNLOAD_RETRY_JITTER_SECONDS: ClassVar[float] = 0.2
    _DOWNLOAD_CHUNK_SIZE_BYTES: ClassVar[int] = 64 * 1024
    _TRANSIENT_HTTP_STATUS: ClassVar[tuple[int, ...]] = (408, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524)

    @classmethod
    @abstractmethod
    async def fetch(cls, url: str) -> MediaPost | None:
        raise NotImplementedError

    @classmethod
    async def safe_fetch(cls, url: str) -> MediaPost | None:
        try:
            return await cls.fetch(url)
        except asyncio.CancelledError:
            raise
        except TimeoutError:
            await logger.awarning("[Medias] Provider fetch timed out", provider=cls.name, source_url=url)
            return None
        except Exception:  # ruff: ignore[blind-except]
            await logger.aexception("[Medias] Provider fetch failed", provider=cls.name, source_url=url)
            return None

    @classmethod
    async def download_media(
        cls,
        sources: Sequence[MediaSource],
        *,
        filename_prefix: str,
        max_size: int | None = TELEGRAM_MEDIA_MAX_FILE_SIZE_BYTES,
        log_label: str | None = None,
    ) -> list[MediaItem]:
        if not sources:
            return []

        label = log_label or cls.name
        requests = [
            MediaDownloadRequest(
                source=source, index=index, filename_prefix=filename_prefix, max_size=max_size, label=label
            )
            for index, source in enumerate(sources, start=1)
        ]
        return await cls._process_downloads(requests)

    @classmethod
    async def _process_downloads(cls, requests: Sequence[MediaDownloadRequest]) -> list[MediaItem]:
        results: list[MediaItem | None] = [None] * len(requests)
        cache_keys = [media_source_cache_key(request.source.url) for request in requests]
        cached_payloads = await get_cached_file_payloads(cache_keys)
        pending_requests: list[MediaDownloadRequest] = []

        for request, cached_payload in zip(requests, cached_payloads, strict=True):
            cached_file_id = cached_payload.get("file_id") if cached_payload else None
            if isinstance(cached_file_id, str) and cached_file_id:
                results[request.index - 1] = cls._cached_media_item(request, cached_file_id)
            else:
                pending_requests.append(request)

        async with asyncio.TaskGroup() as tg:
            for request in pending_requests:
                tg.create_task(cls._download_worker(request, results))

        await logger.adebug(
            "[Medias] Download batch finished",
            provider=requests[0].label,
            source_count=len(requests),
            source_cache_hits=len(requests) - len(pending_requests),
            downloaded_count=sum(isinstance(item.file, BufferedInputFile) for item in results if item is not None),
        )
        return [item for item in results if item is not None]

    @staticmethod
    def _cached_media_item(request: MediaDownloadRequest, file_id: str) -> MediaItem:
        source = request.source
        return MediaItem(
            kind=source.kind,
            file=file_id,
            filename=f"{request.filename_prefix}_{request.index}",
            source_url=source.url,
            duration=source.duration,
            width=source.width,
            height=source.height,
        )

    @classmethod
    async def _get_cached_media_item(cls, request: MediaDownloadRequest) -> MediaItem | None:
        cached_payload = await get_cached_file_payload(media_source_cache_key(request.source.url))
        cached_file_id = cached_payload.get("file_id") if cached_payload else None
        if not isinstance(cached_file_id, str) or not cached_file_id:
            return None
        return cls._cached_media_item(request, cached_file_id)

    @classmethod
    async def _download_worker(cls, request: MediaDownloadRequest, results_list: list[MediaItem | None]) -> None:
        try:
            item = await cls._download_source(request)
            results_list[request.index - 1] = item
        except asyncio.CancelledError:
            raise
        except TimeoutError:
            await logger.awarning(
                "[Medias] Download source timed out",
                provider=request.label,
                source_url=request.source.url,
                source_index=request.index,
                source_kind=request.source.kind.value,
            )
        except Exception:  # ruff: ignore[blind-except]
            await logger.aexception(
                "[Medias] Download worker failed",
                provider=request.label,
                source_url=request.source.url,
                source_index=request.index,
                source_kind=request.source.kind.value,
            )

    @classmethod
    async def _download_source(cls, request: MediaDownloadRequest) -> MediaItem | None:
        source = request.source
        payload_result = await cls._fetch_payload_with_retry(
            source.url, request, stage="source", max_size=request.max_size
        )
        if payload_result is None:
            return None

        payload, content_type = payload_result
        extension = cls._guess_extension(source.url, content_type, source.kind)

        if not extension:
            extension = cls._guess_extension(source.url, "", source.kind)

        thumbnail: InputFile | None = None
        if source.thumbnail_url and source.kind == MediaKind.VIDEO:
            thumbnail = await cls._download_thumbnail(source.thumbnail_url, request)

        filename = f"{request.filename_prefix}_{request.index}{extension}"

        return MediaItem(
            kind=source.kind,
            file=BufferedInputFile(payload, filename),
            filename=filename,
            source_url=source.url,
            thumbnail=thumbnail,
            duration=source.duration,
            width=source.width,
            height=source.height,
        )

    @classmethod
    def _should_retry_status(cls, status_code: int) -> bool:
        return status_code in cls._TRANSIENT_HTTP_STATUS

    @classmethod
    async def _sleep_before_retry(cls, attempt: int) -> None:
        backoff = cls._DOWNLOAD_RETRY_BASE_DELAY_SECONDS * (2 ** max(0, attempt - 1))
        jitter = random.uniform(0.0, cls._DOWNLOAD_RETRY_JITTER_SECONDS)
        await asyncio.sleep(backoff + jitter)

    @classmethod
    async def _fetch_payload_with_retry(
        cls,
        url: str,
        request: MediaDownloadRequest,
        *,
        stage: Literal["source", "thumbnail"],
        max_size: int | None = None,
    ) -> tuple[bytes, str] | None:
        session = await HTTPClient.get_session()
        max_attempts = cls._DOWNLOAD_RETRY_ATTEMPTS
        log_context = {
            "provider": request.label,
            "source_url": url,
            "source_index": request.index,
            "source_kind": request.source.kind.value,
            "stage": stage,
        }
        for attempt in range(1, max_attempts + 1):
            try:
                async with (
                    MEDIA_DOWNLOAD_SLOTS,
                    session.get(url, headers=cls._DEFAULT_HEADERS, timeout=cls._DEFAULT_TIMEOUT) as response,
                ):
                    if response.status != 200:
                        if attempt >= max_attempts or not cls._should_retry_status(response.status):
                            await logger.adebug(
                                "[Medias] Download rejected by upstream", **log_context, status=response.status
                            )
                            return None
                    elif max_size and (content_len := response.content_length) and content_len > max_size:
                        await logger.adebug("[Medias] Download exceeded size limit", **log_context, size=content_len)
                        return None
                    else:
                        payload = await cls._read_payload(response, max_size=max_size)
                        if payload is None:
                            await logger.adebug(
                                "[Medias] Download exceeded size limit while streaming",
                                **log_context,
                                max_size=max_size,
                            )
                            return None
                        return payload, response.headers.get("Content-Type", "")

                await cls._sleep_before_retry(attempt)
            except asyncio.CancelledError:
                raise
            except TimeoutError:
                if attempt < max_attempts:
                    await cls._sleep_before_retry(attempt)
                    continue

                await logger.awarning("[Medias] Download timed out", **log_context, attempts=attempt)
                return None
            except aiohttp.ClientError as error:
                if attempt < max_attempts:
                    await cls._sleep_before_retry(attempt)
                    continue

                if isinstance(error, aiohttp.ClientPayloadError):
                    await logger.awarning("[Medias] Download payload truncated", **log_context, attempts=attempt)
                else:
                    await logger.awarning(
                        "[Medias] Download network error",
                        **log_context,
                        attempts=attempt,
                        error_type=type(error).__name__,
                        error=str(error),
                    )
                return None
            except Exception:  # ruff: ignore[blind-except]
                await logger.aexception("[Medias] Download unexpected error", **log_context)
                return None

        return None

    @classmethod
    async def _read_payload(cls, response: aiohttp.ClientResponse, *, max_size: int | None) -> bytes | None:
        if max_size is None:
            return await response.read()

        payload = bytearray()
        total_size = 0
        async for chunk in response.content.iter_chunked(cls._DOWNLOAD_CHUNK_SIZE_BYTES):
            if not chunk:
                continue

            total_size += len(chunk)
            if total_size > max_size:
                return None

            payload.extend(chunk)

        return bytes(payload)

    @classmethod
    async def _fetch_payload_to_path_with_retry(
        cls, url: str, request: MediaDownloadRequest, destination: Path, *, max_size: int | None
    ) -> int | None:
        session = await HTTPClient.get_session()
        log_context = {
            "provider": request.label,
            "source_url": url,
            "source_index": request.index,
            "source_kind": request.source.kind.value,
            "stage": "source",
        }
        for attempt in range(1, cls._DOWNLOAD_RETRY_ATTEMPTS + 1):
            await cls._remove_path(destination)
            try:
                async with (
                    MEDIA_DOWNLOAD_SLOTS,
                    session.get(url, headers=cls._DEFAULT_HEADERS, timeout=cls._DEFAULT_TIMEOUT) as response,
                ):
                    if response.status != 200:
                        if attempt >= cls._DOWNLOAD_RETRY_ATTEMPTS or not cls._should_retry_status(response.status):
                            await logger.adebug(
                                "[Medias] Download rejected by upstream", **log_context, status=response.status
                            )
                            return None
                    elif max_size and (content_len := response.content_length) and content_len > max_size:
                        await logger.adebug("[Medias] Download exceeded size limit", **log_context, size=content_len)
                        return None
                    else:
                        total_size = await cls._write_response_to_path(response, destination, max_size=max_size)
                        if total_size is None:
                            await cls._remove_path(destination)
                            await logger.adebug(
                                "[Medias] Download exceeded size limit while streaming",
                                **log_context,
                                max_size=max_size,
                            )
                            return None
                        return total_size

                await cls._sleep_before_retry(attempt)
            except asyncio.CancelledError:
                await cls._remove_path(destination)
                raise
            except TimeoutError:
                await cls._remove_path(destination)
                if attempt < cls._DOWNLOAD_RETRY_ATTEMPTS:
                    await cls._sleep_before_retry(attempt)
                    continue
                await logger.awarning("[Medias] Download timed out", **log_context, attempts=attempt)
                return None
            except aiohttp.ClientError as error:
                await cls._remove_path(destination)
                if attempt < cls._DOWNLOAD_RETRY_ATTEMPTS:
                    await cls._sleep_before_retry(attempt)
                    continue
                if isinstance(error, aiohttp.ClientPayloadError):
                    await logger.awarning("[Medias] Download payload truncated", **log_context, attempts=attempt)
                else:
                    await logger.awarning(
                        "[Medias] Download network error",
                        **log_context,
                        attempts=attempt,
                        error_type=type(error).__name__,
                        error=str(error),
                    )
                return None
            except OSError as error:
                await cls._remove_path(destination)
                await logger.awarning(
                    "[Medias] Download file error", **log_context, error_type=type(error).__name__, error=str(error)
                )
                return None

        return None

    @classmethod
    async def _write_response_to_path(
        cls, response: aiohttp.ClientResponse, destination: Path, *, max_size: int | None
    ) -> int | None:
        total_size = 0
        async with aiofiles.open(destination, "wb") as output_file:
            async for chunk in response.content.iter_chunked(cls._DOWNLOAD_CHUNK_SIZE_BYTES):
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

    @classmethod
    async def _download_thumbnail(cls, url: str, request: MediaDownloadRequest) -> InputFile | None:
        payload_result = await cls._fetch_payload_with_retry(url, request, stage="thumbnail")
        if payload_result is None:
            return None

        payload, content_type = payload_result
        ext = cls._guess_extension(url, content_type, MediaKind.PHOTO)
        filename = f"{request.filename_prefix}_{request.index}_thumb{ext}"
        return BufferedInputFile(payload, filename)

    @staticmethod
    def _guess_extension(url: str, content_type: str, kind: MediaKind) -> str:
        path = Path(urlparse(url).path)
        if path.suffix:
            return path.suffix

        if content_type:
            ext = mimetypes.guess_extension(content_type.split(";", maxsplit=1)[0].strip())
            if ext:
                return ".jpg" if ext == ".jpe" else ext

        return ".mp4" if kind == MediaKind.VIDEO else ".jpg"

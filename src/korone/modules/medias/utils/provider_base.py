from __future__ import annotations

import asyncio
import mimetypes
import random
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Literal
from urllib.parse import urlparse

import aiohttp
from aiogram.types import BufferedInputFile

from korone.logger import get_logger
from korone.modules.medias.utils.url import normalize_media_url
from korone.modules.utils_.file_id_cache import get_cached_file_payload, make_file_id_cache_key
from korone.utils.aiohttp_session import HTTPClient

from .types import MediaItem, MediaKind

type FetchPayloadAttemptResult = tuple[bytes, str] | Literal["retry"] | None

if TYPE_CHECKING:
    import re
    from collections.abc import Sequence

    from aiogram.types import InputFile

    from .types import MediaPost, MediaSource

logger = get_logger(__name__)


class MediaProvider(ABC):
    name: ClassVar[str]
    website: ClassVar[str]
    pattern: ClassVar[re.Pattern[str]]

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
    _MEDIA_SOURCE_CACHE_NAMESPACE: ClassVar[str] = "media-source"
    _DOWNLOAD_RETRY_ATTEMPTS: ClassVar[int] = 3
    _DOWNLOAD_RETRY_BASE_DELAY_SECONDS: ClassVar[float] = 0.35
    _DOWNLOAD_RETRY_JITTER_SECONDS: ClassVar[float] = 0.2
    _DOWNLOAD_CHUNK_SIZE_BYTES: ClassVar[int] = 64 * 1024
    _TRANSIENT_HTTP_STATUS: ClassVar[tuple[int, ...]] = (408, 429, 500, 502, 503, 504, 520, 521, 522, 523, 524)

    @classmethod
    def extract_urls(cls, text: str) -> list[str]:
        return [match.group(0) for match in cls.pattern.finditer(text)]

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
        except Exception:  # noqa: BLE001
            await logger.aexception("[Medias] Provider fetch failed", provider=cls.name, source_url=url)
            return None

    @classmethod
    async def download_media(
        cls,
        sources: Sequence[MediaSource],
        *,
        filename_prefix: str,
        max_size: int | None = None,
        log_label: str | None = None,
    ) -> list[MediaItem]:
        if not sources:
            return []

        label = log_label or cls.name
        return await cls._process_downloads(sources, filename_prefix, max_size, label)

    @classmethod
    async def _process_downloads(
        cls, sources: Sequence[MediaSource], prefix: str, max_size: int | None, label: str
    ) -> list[MediaItem]:
        results: list[MediaItem | None] = [None] * len(sources)

        async with asyncio.TaskGroup() as tg:
            for source_index, source in enumerate(sources, start=1):
                tg.create_task(cls._download_worker(source_index, source, prefix, max_size, label, results))

        return [item for item in results if item is not None]

    @classmethod
    async def _download_worker(
        cls,
        source_index: int,
        source: MediaSource,
        prefix: str,
        max_size: int | None,
        label: str,
        results_list: list[MediaItem | None],
    ) -> None:
        try:
            item = await cls._download_source(source, source_index, prefix, max_size, label)
            results_list[source_index - 1] = item
        except asyncio.CancelledError:
            raise
        except TimeoutError:
            await logger.awarning(
                "[Medias] Download source timed out",
                provider=label,
                source_url=source.url,
                source_index=source_index,
                source_kind=source.kind.value,
            )
        except Exception:  # noqa: BLE001
            await logger.aexception(
                "[Medias] Download worker failed",
                provider=label,
                source_url=source.url,
                source_index=source_index,
                source_kind=source.kind.value,
            )

    @classmethod
    async def _download_source(
        cls, source: MediaSource, index: int, prefix: str, max_size: int | None, label: str
    ) -> MediaItem | None:
        cache_key = cls._media_source_cache_key(source.url)
        cached_payload = await get_cached_file_payload(cache_key)
        if cached_payload:
            cached_file_id = cached_payload.get("file_id")
            if isinstance(cached_file_id, str) and cached_file_id:
                return MediaItem(
                    kind=source.kind,
                    file=cached_file_id,
                    filename=f"{prefix}_{index}",
                    source_url=source.url,
                    duration=source.duration,
                    width=source.width,
                    height=source.height,
                )

        payload_result = await cls._fetch_payload_with_retry(
            source.url, label=label, stage="source", max_size=max_size, source_kind=source.kind, source_index=index
        )
        if payload_result is None:
            return None

        payload, content_type = payload_result
        extension = cls._guess_extension(source.url, content_type, source.kind)

        if not extension:
            extension = cls._guess_extension(source.url, "", source.kind)

        thumbnail: InputFile | None = None
        if source.thumbnail_url and source.kind == MediaKind.VIDEO:
            thumbnail = await cls._download_thumbnail(source.thumbnail_url, label, index, prefix)

        filename = f"{prefix}_{index}{extension}"

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
    def _media_source_cache_key(cls, source_url: str) -> str:
        cache_identifier = normalize_media_url(source_url) or source_url.strip() or source_url
        return make_file_id_cache_key(cls._MEDIA_SOURCE_CACHE_NAMESPACE, cache_identifier)

    @classmethod
    def _build_download_log_context(
        cls,
        *,
        label: str,
        url: str,
        attempts: int | None = None,
        stage: Literal["source", "thumbnail"] | None = None,
        source_kind: MediaKind | None = None,
        source_index: int | None = None,
    ) -> dict[str, object]:
        context: dict[str, object] = {"provider": label, "source_url": url}
        if attempts is not None:
            context["attempts"] = attempts
        if source_index is not None:
            context["source_index"] = source_index
        if source_kind is not None:
            context["source_kind"] = source_kind.value
        if stage is not None:
            context["stage"] = stage
        return context

    @staticmethod
    def _timeout_log_message(stage: Literal["source", "thumbnail"]) -> str:
        return "[Medias] Download source timed out" if stage == "source" else "[Medias] Download thumbnail timed out"

    @staticmethod
    def _payload_truncated_log_message(stage: Literal["source", "thumbnail"]) -> str:
        return (
            "[Medias] Download source payload truncated"
            if stage == "source"
            else "[Medias] Download thumbnail payload truncated"
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
        *,
        label: str,
        stage: Literal["source", "thumbnail"],
        max_size: int | None = None,
        source_kind: MediaKind | None = None,
        source_index: int | None = None,
    ) -> tuple[bytes, str] | None:
        session = await HTTPClient.get_session()
        max_attempts = cls._DOWNLOAD_RETRY_ATTEMPTS
        for attempt in range(1, max_attempts + 1):
            try:
                async with session.get(url, headers=cls._DEFAULT_HEADERS, timeout=cls._DEFAULT_TIMEOUT) as response:
                    attempt_result = await cls._handle_payload_attempt(
                        response=response,
                        url=url,
                        label=label,
                        attempt=attempt,
                        max_attempts=max_attempts,
                        max_size=max_size,
                    )
                if attempt_result != "retry":
                    return attempt_result
                await cls._sleep_before_retry(attempt)
            except asyncio.CancelledError:
                raise
            except TimeoutError:
                if attempt < max_attempts:
                    await cls._sleep_before_retry(attempt)
                    continue

                await cls._log_timeout_exhausted(
                    label=label,
                    url=url,
                    stage=stage,
                    attempts=attempt,
                    source_kind=source_kind,
                    source_index=source_index,
                )
                return None
            except aiohttp.ClientError as error:
                if attempt < max_attempts:
                    await cls._sleep_before_retry(attempt)
                    continue

                await cls._log_client_error_exhausted(
                    label=label,
                    url=url,
                    stage=stage,
                    error=error,
                    attempts=attempt,
                    source_kind=source_kind,
                    source_index=source_index,
                )
                return None
            except Exception:  # noqa: BLE001
                await cls._log_unexpected_download_error(
                    label=label, url=url, stage=stage, source_kind=source_kind, source_index=source_index
                )
                return None

        return None

    @classmethod
    async def _handle_payload_attempt(
        cls,
        *,
        response: aiohttp.ClientResponse,
        url: str,
        label: str,
        attempt: int,
        max_attempts: int,
        max_size: int | None,
    ) -> FetchPayloadAttemptResult:
        if response.status != 200:
            if attempt < max_attempts and cls._should_retry_status(response.status):
                return "retry"
            await logger.adebug(f"[{label}] HTTP {response.status}", url=url)
            return None

        if max_size and (content_len := response.content_length) and content_len > max_size:
            await logger.adebug(f"[{label}] Media too large", size=content_len)
            return None

        payload = await cls._read_payload(response, label=label, max_size=max_size)
        if payload is None:
            return None

        return payload, response.headers.get("Content-Type", "")

    @classmethod
    async def _log_timeout_exhausted(
        cls,
        *,
        label: str,
        url: str,
        stage: Literal["source", "thumbnail"],
        attempts: int,
        source_kind: MediaKind | None,
        source_index: int | None,
    ) -> None:
        await logger.awarning(
            cls._timeout_log_message(stage),
            **cls._build_download_log_context(
                label=label, url=url, attempts=attempts, source_kind=source_kind, source_index=source_index
            ),
        )

    @classmethod
    async def _log_client_error_exhausted(
        cls,
        *,
        label: str,
        url: str,
        stage: Literal["source", "thumbnail"],
        error: aiohttp.ClientError,
        attempts: int,
        source_kind: MediaKind | None,
        source_index: int | None,
    ) -> None:
        log_context = cls._build_download_log_context(
            label=label, url=url, attempts=attempts, source_kind=source_kind, source_index=source_index
        )

        if isinstance(error, aiohttp.ClientPayloadError):
            await logger.awarning(cls._payload_truncated_log_message(stage), **log_context)
            return

        await logger.awarning(
            "[Medias] Download network error",
            **log_context,
            stage=stage,
            error_type=type(error).__name__,
            error=str(error),
        )

    @classmethod
    async def _log_unexpected_download_error(
        cls,
        *,
        label: str,
        url: str,
        stage: Literal["source", "thumbnail"],
        source_kind: MediaKind | None,
        source_index: int | None,
    ) -> None:
        await logger.aexception(
            "[Medias] Download unexpected error",
            **cls._build_download_log_context(
                label=label, url=url, stage=stage, source_kind=source_kind, source_index=source_index
            ),
        )

    @classmethod
    async def _read_payload(cls, response: aiohttp.ClientResponse, *, label: str, max_size: int | None) -> bytes | None:
        if max_size is None:
            return await response.read()

        payload = bytearray()
        total_size = 0
        async for chunk in response.content.iter_chunked(cls._DOWNLOAD_CHUNK_SIZE_BYTES):
            if not chunk:
                continue

            total_size += len(chunk)
            if total_size > max_size:
                await logger.adebug(f"[{label}] Media too large", size=total_size)
                return None

            payload.extend(chunk)

        return bytes(payload)

    @classmethod
    async def _download_thumbnail(cls, url: str, label: str, index: int, prefix: str) -> InputFile | None:
        payload_result = await cls._fetch_payload_with_retry(url, label=label, stage="thumbnail", source_index=index)
        if payload_result is None:
            return None

        payload, content_type = payload_result
        ext = cls._guess_extension(url, content_type, MediaKind.PHOTO)
        filename = f"{prefix}_{index}_thumb{ext}"
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

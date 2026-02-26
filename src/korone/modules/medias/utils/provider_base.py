from __future__ import annotations

import asyncio
import mimetypes
from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar
from urllib.parse import urlparse

import aiohttp
from aiogram.types import BufferedInputFile

from korone.logger import get_logger
from korone.modules.medias.utils.url import normalize_media_url
from korone.modules.utils_.file_id_cache import get_cached_file_payload, make_file_id_cache_key
from korone.utils.aiohttp_session import HTTPClient

from .types import MediaItem, MediaKind

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

    @classmethod
    def extract_urls(cls, text: str) -> list[str]:
        return [match.group(0) for match in cls.pattern.finditer(text)]

    @classmethod
    @abstractmethod
    async def fetch(cls, url: str) -> MediaPost | None:
        raise NotImplementedError

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
            for i, source in enumerate(sources):
                tg.create_task(cls._download_worker(i, source, prefix, max_size, label, results))

        return [item for item in results if item is not None]

    @classmethod
    async def _download_worker(
        cls,
        index: int,
        source: MediaSource,
        prefix: str,
        max_size: int | None,
        label: str,
        results_list: list[MediaItem | None],
    ) -> None:
        try:
            item = await cls._download_source(source, index + 1, prefix, max_size, label)
            results_list[index] = item
        except Exception as e:  # noqa: BLE001
            await logger.aerror(f"[{label}] Unexpected worker error", error=str(e), url=source.url)

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

        try:
            session = await HTTPClient.get_session()
            async with session.get(source.url, headers=cls._DEFAULT_HEADERS, timeout=cls._DEFAULT_TIMEOUT) as response:
                if response.status != 200:
                    await logger.adebug(f"[{label}] HTTP {response.status}", url=source.url)
                    return None

                if max_size and (content_len := response.content_length) and content_len > max_size:
                    await logger.adebug(f"[{label}] Media too large", size=content_len)
                    return None

                payload = await response.read()

                if max_size and len(payload) > max_size:
                    return None

                content_type = response.headers.get("Content-Type", "")
                extension = cls._guess_extension(source.url, content_type, source.kind)

        except aiohttp.ClientError as exc:
            await logger.aerror(f"[{label}] Network error", error=str(exc))
            return None

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
    async def _download_thumbnail(cls, url: str, label: str, index: int, prefix: str) -> InputFile | None:
        try:
            session = await HTTPClient.get_session()
            async with session.get(url, headers=cls._DEFAULT_HEADERS, timeout=cls._DEFAULT_TIMEOUT) as response:
                if response.status != 200:
                    return None
                payload = await response.read()

                ext = cls._guess_extension(url, response.headers.get("Content-Type", ""), MediaKind.PHOTO)
                filename = f"{prefix}_{index}_thumb{ext}"
                return BufferedInputFile(payload, filename)
        except aiohttp.ClientError:
            return None

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

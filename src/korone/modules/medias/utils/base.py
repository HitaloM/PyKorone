from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar
from urllib.parse import urlparse

import aiohttp
from aiogram.types import BufferedInputFile
from anyio import create_task_group

from korone.logger import get_logger

if TYPE_CHECKING:
    import re

    from aiogram.types import InputFile


logger = get_logger(__name__)


class MediaKind(StrEnum):
    PHOTO = "photo"
    VIDEO = "video"


@dataclass(frozen=True, slots=True)
class MediaItem:
    kind: MediaKind
    file: InputFile
    filename: str
    thumbnail: InputFile | None = None
    duration: int | None = None
    width: int | None = None
    height: int | None = None


@dataclass(frozen=True, slots=True)
class MediaPost:
    author_name: str
    author_handle: str
    text: str
    url: str
    website: str
    media: list[MediaItem]


@dataclass(frozen=True, slots=True)
class MediaSource:
    kind: MediaKind
    url: str
    thumbnail_url: str | None = None
    duration: int | None = None
    width: int | None = None
    height: int | None = None


class MediaProvider(ABC):
    name: ClassVar[str]
    website: ClassVar[str]
    pattern: ClassVar[re.Pattern[str]]

    @classmethod
    def extract_urls(cls, text: str) -> list[str]:
        return [match.group(0) for match in cls.pattern.finditer(text)]

    @classmethod
    @abstractmethod
    async def fetch(cls, url: str) -> MediaPost | None:
        raise NotImplementedError

    @classmethod
    async def _download_media_sources(
        cls,
        sources: list[MediaSource],
        *,
        timeout: int,  # noqa: ASYNC109
        filename_prefix: str,
        max_size: int | None = None,
        log_label: str | None = None,
    ) -> list[MediaItem]:
        if not sources:
            return []

        headers = {"user-agent": "KoroneBot/1.0"}
        results: list[MediaItem | None] = [None] * len(sources)

        async def _download_one(index: int, source: MediaSource, session: aiohttp.ClientSession) -> None:
            item = await cls._download_source(source, index, session, filename_prefix, max_size, log_label)
            results[index] = item

        client_timeout = aiohttp.ClientTimeout(total=timeout)
        async with aiohttp.ClientSession(timeout=client_timeout, headers=headers) as session, create_task_group() as tg:
            for index, source in enumerate(sources, start=1):
                tg.start_soon(_download_one, index - 1, source, session)

        return [item for item in results if item]

    @classmethod
    async def _download_source(
        cls,
        source: MediaSource,
        index: int,
        session: aiohttp.ClientSession,
        filename_prefix: str,
        max_size: int | None,
        log_label: str | None,
    ) -> MediaItem | None:
        label = log_label or cls.name
        try:
            async with session.get(source.url) as response:
                if response.status != 200:
                    await logger.adebug(f"[{label}] Failed to download media", status=response.status, url=source.url)
                    return None

                content_length = response.content_length
                if max_size and content_length and content_length > max_size:
                    await logger.adebug(f"[{label}] Media too large for Telegram", size=content_length, url=source.url)
                    return None

                payload = await response.read()
        except aiohttp.ClientError as exc:
            await logger.aerror(f"[{label}] Media download error", error=str(exc))
            return None

        thumbnail = None
        if source.thumbnail_url and source.kind == MediaKind.VIDEO:
            thumbnail = await cls._download_thumbnail(source.thumbnail_url, session, label, index, filename_prefix)

        filename = cls._make_media_filename(source.url, source.kind, index, filename_prefix)
        return MediaItem(
            kind=source.kind,
            file=BufferedInputFile(payload, filename),
            filename=filename,
            thumbnail=thumbnail,
            duration=source.duration,
            width=source.width,
            height=source.height,
        )

    @classmethod
    async def _download_thumbnail(
        cls, url: str, session: aiohttp.ClientSession, label: str, index: int, filename_prefix: str
    ) -> InputFile | None:
        try:
            async with session.get(url) as response:
                if response.status != 200:
                    await logger.adebug(f"[{label}] Failed to download thumbnail", status=response.status, url=url)
                    return None
                payload = await response.read()
        except aiohttp.ClientError as exc:
            await logger.aerror(f"[{label}] Thumbnail download error", error=str(exc))
            return None

        filename = cls._make_thumbnail_filename(url, index, filename_prefix)
        return BufferedInputFile(payload, filename)

    @staticmethod
    def _make_media_filename(url: str, kind: MediaKind, index: int, prefix: str) -> str:
        parsed = urlparse(url)
        suffix = Path(parsed.path).suffix
        if not suffix:
            suffix = ".mp4" if kind == MediaKind.VIDEO else ".jpg"
        return f"{prefix}_{index}{suffix}"

    @staticmethod
    def _make_thumbnail_filename(url: str, index: int, prefix: str) -> str:
        parsed = urlparse(url)
        suffix = Path(parsed.path).suffix
        if not suffix:
            suffix = ".jpg"
        return f"{prefix}_{index}_thumb{suffix}"

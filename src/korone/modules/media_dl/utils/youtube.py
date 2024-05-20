# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio
import io
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import httpx
import yt_dlp

from korone.utils.logging import log


class YTDLError(Exception):
    pass


class DownloadError(YTDLError):
    pass


class InfoExtractionError(YTDLError):
    pass


@dataclass(frozen=True, slots=True)
class VideoInfo:
    title: str
    id: str
    thumbnail: io.BytesIO
    url: str
    duration: int
    view_count: int
    like_count: int
    uploader: str
    height: int
    width: int


class YTDL:
    __slots__ = ("http", "options")

    def __init__(self, options: dict[str, Any]) -> None:
        self.options = options
        self.http = httpx.AsyncClient(http2=True, timeout=10.0)

    async def process_url(
        self, url: str, download: bool
    ) -> tuple[dict[str, Any] | None, str | None]:
        loop = asyncio.get_event_loop()
        try:
            file_path = None
            with yt_dlp.YoutubeDL(self.options) as ydl:
                info = await loop.run_in_executor(None, ydl.extract_info, url, download)
                if download:
                    file_path = ydl.prepare_filename(info)

                return info, file_path
        except yt_dlp.DownloadError as err:
            log.error("Error downloading content from '%s'", url, exc_info=True)
            raise DownloadError(err.msg) from err

    async def download(self, url: str, options: dict[str, Any]) -> tuple[VideoInfo, str]:
        self.options.update(options)
        info, file_path = await self.process_url(url, download=True)
        if not info or not file_path:
            msg = "Failed to download content!"
            raise DownloadError(msg)

        log.debug("Download completed for %s, saved to %s", url, file_path)

        info = await self.generate_videoinfo(info)
        return info, file_path

    async def get_info(self, url: str, options: dict[str, Any]) -> VideoInfo:
        self.options.update(options)
        info, _ = await self.process_url(url, download=False)
        if not info:
            msg = "Failed to extract video info!"
            raise InfoExtractionError(msg)

        log.debug("Information extracted for %s", url)
        return await self.generate_videoinfo(info)

    async def generate_videoinfo(self, info: dict[str, Any]) -> VideoInfo:
        thumbnail = info.get("thumbnail")
        if not thumbnail:
            msg = "Thumbnail not found"
            raise InfoExtractionError(msg)

        r = await self.http.get(thumbnail)
        thumbnail = io.BytesIO(r.content)
        thumbnail.name = "thumbnail.png"

        return VideoInfo(
            title=info.get("title", ""),
            id=info.get("id", ""),
            thumbnail=thumbnail,
            url=info.get("webpage_url", ""),
            duration=info.get("duration", 0),
            view_count=info.get("view_count", 0),
            like_count=info.get("like_count", 0),
            uploader=info.get("uploader", ""),
            height=info.get("height", 0),
            width=info.get("width", 0),
        )


class YtdlpManager:
    __slots__ = ("audio_options", "file_path", "video_options", "ytdl")

    def __init__(self) -> None:
        self.ytdl = YTDL({"quiet": True, "no_warnings": True, "format": "best"})
        self.file_path: str | None = None
        timestamp = datetime.now(UTC).strftime("%d%m%Y%H%M%S")

        self.audio_options = {
            "quiet": True,
            "no_warnings": True,
            "format_sort": ["size"],
            "outtmpl": f"downloads/%(title)s [%(id)s] {timestamp}.%(ext)s",
            "format": "bestaudio[filesize<=300M][ext=m4a]",
        }
        self.video_options = {
            "quiet": True,
            "no_warnings": True,
            "format_sort": ["size"],
            "outtmpl": f"downloads/%(title)s [%(id)s] {timestamp}.%(ext)s",
            "format": "mergeall[filesize<=300M][height<=1080][ext=mp4]",
        }

    async def get_video_info(self, url: str) -> VideoInfo:
        return await self.ytdl.get_info(url, {})

    async def download(self, url: str, options: dict[str, Any]) -> tuple[VideoInfo, str]:
        info, file_path = await self.ytdl.download(url, options)
        self.file_path = file_path
        return info, file_path

    async def download_video(self, url: str) -> tuple[VideoInfo, str]:
        return await self.download(url, self.video_options)

    async def download_audio(self, url: str) -> tuple[VideoInfo, str]:
        return await self.download(url, self.audio_options)

    def clear(self) -> None:
        if self.file_path:
            file = Path(self.file_path)
            file.unlink(missing_ok=True)
            log.debug("Removed file %s", self.file_path)
            self.file_path = None

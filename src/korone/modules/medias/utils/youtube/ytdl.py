# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yt_dlp

from korone.modules.medias.utils.files import resize_thumbnail
from korone.modules.medias.utils.youtube.types import VideoInfo
from korone.utils.logging import logger


class YTDLError(Exception):
    pass


class DownloadError(YTDLError):
    pass


class InfoExtractionError(YTDLError):
    pass


class YTDL:
    __slots__ = ("download", "file_path", "options")

    def __init__(self, download: bool) -> None:
        self.options = {"quiet": True, "no_warnings": True}
        self.download: bool = download
        self.file_path: str | None = None

    async def process_url(self, url: str) -> dict[str, Any] | None:
        try:
            self.file_path = None
            with yt_dlp.YoutubeDL(self.options) as ydl:
                info = await asyncio.to_thread(ydl.extract_info, url, self.download)
                if self.download:
                    self.file_path = Path(ydl.prepare_filename(info)).as_posix()
                return info
        except yt_dlp.DownloadError as e:
            await logger.aexception("Error downloading content from '%s'", url)
            raise DownloadError(e.msg) from e

    async def _download(self, url: str, options: dict[str, Any]) -> VideoInfo:
        self.options.update(options)
        self.download = True
        info = await self.process_url(url)
        if not info or not self.file_path:
            msg = "Failed to download content!"
            raise DownloadError(msg)

        await logger.adebug("Download completed for %s, saved to %s", url, self.file_path)

        return await self.generate_videoinfo(info)

    async def get_info(self, url: str, options: dict[str, Any]) -> VideoInfo:
        self.options.update(options)
        self.download = False
        try:
            info = await self.process_url(url)
        except DownloadError as e:
            raise InfoExtractionError(e) from e

        if not info:
            msg = "Failed to extract video info!"
            raise InfoExtractionError(msg)

        await logger.adebug("Information extracted for %s", url)
        return await self.generate_videoinfo(info)

    async def generate_videoinfo(self, info: dict[str, Any]) -> VideoInfo:
        thumbnail = None
        if self.download and self.file_path:
            thumbnail = Path(self.file_path).with_suffix(".jpeg").as_posix()
            await asyncio.to_thread(resize_thumbnail, thumbnail)

        info["thumbnail"] = thumbnail
        info["uploader"] = info.get("artist") or info.get("uploader", "")

        return VideoInfo.model_validate(info)


class YtdlpManager:
    __slots__ = ("audio_options", "file_path", "thumbnail_path", "timestamp", "video_options")

    def __init__(self) -> None:
        self.thumbnail_path: str | None = None
        self.file_path: str | None = None
        self.timestamp = datetime.now(UTC).strftime("%d%m%Y%H%M%S")

        self.audio_options = self._get_options("bestaudio[filesize<=300M][ext=m4a]")
        self.video_options = self._get_options(
            "mergeall[filesize<=300M][height<=1080][ext=mp4]+140"
        )

    def _get_options(self, format_str: str) -> dict[str, Any]:
        return {
            "quiet": True,
            "no_warnings": True,
            "format_sort": ["size"],
            "postprocessors": [
                {
                    "key": "FFmpegThumbnailsConvertor",
                    "format": "jpeg",
                },
            ],
            "writethumbnail": True,
            "outtmpl": f"downloads/%(title)s [%(id)s] {self.timestamp}.%(ext)s",
            "format": format_str,
        }

    @staticmethod
    async def get_video_info(url: str) -> VideoInfo:
        ytdl = YTDL(download=False)
        return await ytdl.get_info(url, {})

    async def download(self, url: str, options: dict[str, Any]) -> VideoInfo:
        ytdl = YTDL(download=True)
        info = await ytdl._download(url, options)

        self.thumbnail_path = info.thumbnail.as_posix() if info.thumbnail else None
        self.file_path = ytdl.file_path

        return info

    async def download_video(self, url: str) -> VideoInfo:
        return await self.download(url, self.video_options)

    async def download_audio(self, url: str) -> VideoInfo:
        return await self.download(url, self.audio_options)

    def clear(self) -> None:
        for path in [self.file_path, self.thumbnail_path]:
            if path and Path(path).exists():
                Path(path).unlink(missing_ok=True)
                logger.debug("Removed file %s", path)

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yt_dlp
from anyio import to_thread

from korone.config import ConfigManager
from korone.modules.medias.utils.files import resize_thumbnail
from korone.utils.logging import get_logger

from .types import VideoInfo

logger = get_logger(__name__)

PROXY = ConfigManager.get("korone", "PROXY_URL")


class YTDLError(Exception):
    pass


class DownloadError(YTDLError):
    pass


class InfoExtractionError(YTDLError):
    pass


class YTDL:
    __slots__ = ("download", "file_path", "options")

    def __init__(self, download: bool) -> None:
        self.download = download
        self.file_path = None
        self.options = {
            "quiet": True,
            "no_warnings": True,
            "proxy": PROXY,
        }

    async def process_url(self, url: str) -> dict[str, Any] | None:
        try:
            self.file_path = None
            with yt_dlp.YoutubeDL(self.options) as ydl:
                info = await to_thread.run_sync(ydl.extract_info, url, self.download)
                if self.download:
                    self.file_path = Path(ydl.prepare_filename(info)).as_posix()
                return info
        except yt_dlp.DownloadError as e:
            await logger.aexception("[Medias/YouTube] Download failed: %s", url)
            raise DownloadError(e.msg) from e

    async def get_info(self, url: str, options: dict[str, Any]) -> VideoInfo:
        self.options.update(options)
        self.download = False
        try:
            info = await self.process_url(url)
        except DownloadError as e:
            raise InfoExtractionError(e) from e
        if not info:
            msg = "No info extracted!"
            raise InfoExtractionError(msg)
        await logger.adebug("[Medias/YouTube] Info extracted: %s", url)
        return await self.generate_videoinfo(info)

    async def _download(self, url: str, options: dict[str, Any]) -> VideoInfo:
        self.options.update(options)
        self.download = True
        info = await self.process_url(url)
        if not info or not self.file_path:
            msg = "Download failed!"
            raise DownloadError(msg)
        await logger.adebug("[Medias/YouTube] Downloaded: %s -> %s", url, self.file_path)
        return await self.generate_videoinfo(info)

    async def generate_videoinfo(self, info: dict[str, Any]) -> VideoInfo:
        if info.get("_type") == "playlist":
            if not info.get("entries"):
                msg = "No entries in playlist!"
                raise InfoExtractionError(msg)
            info = info["entries"][0]
        if self.download and self.file_path:
            thumbnail = Path(self.file_path).with_suffix(".jpeg").as_posix()
            await to_thread.run_sync(resize_thumbnail, thumbnail)
            info["thumbnail"] = thumbnail
        info["uploader"] = info.get("artist") or info.get("uploader", "")
        return VideoInfo.model_validate(info)


class YtdlpManager:
    __slots__ = ("audio_options", "file_path", "thumbnail_path", "timestamp", "video_options")

    def __init__(self) -> None:
        self.file_path = None
        self.thumbnail_path = None
        self.timestamp = datetime.now(UTC).strftime("%d%m%Y%H%M%S")
        self.audio_options = self._get_options("bestaudio[filesize<=300M][ext=m4a]")
        self.video_options = self._get_options(
            "mergeall[filesize<=300M][height<=1080][ext=mp4]+140"
        )

    def _get_options(self, fmt: str) -> dict[str, Any]:
        return {
            "quiet": True,
            "no_warnings": True,
            "format_sort": ["size"],
            "postprocessors": [{"key": "FFmpegThumbnailsConvertor", "format": "jpeg"}],
            "writethumbnail": True,
            "outtmpl": f"downloads/%(title)s [%(id)s] {self.timestamp}.%(ext)s",
            "format": fmt,
            "proxy": PROXY,
        }

    @staticmethod
    async def get_video_info(url: str) -> VideoInfo:
        options = {"noplaylist": "ytsearch" not in url}
        ytdl = YTDL(download=False)
        return await ytdl.get_info(url, options)

    async def download(self, url: str, options: dict[str, Any]) -> VideoInfo:
        ytdl = YTDL(download=True)
        info = await ytdl._download(url, options)
        self.file_path = ytdl.file_path
        self.thumbnail_path = (
            Path(self.file_path).with_suffix(".jpeg").as_posix() if self.file_path else None
        )
        return info

    async def download_video(self, url: str) -> VideoInfo:
        return await self.download(url, self.video_options)

    async def download_audio(self, url: str) -> VideoInfo:
        return await self.download(url, self.audio_options)

    def clear(self) -> None:
        for path in [self.file_path, self.thumbnail_path]:
            if path and Path(path).exists():
                Path(path).unlink(missing_ok=True)
                logger.debug("[Medias/YouTube] Removed %s", path)

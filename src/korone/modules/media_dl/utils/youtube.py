# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yt_dlp
from PIL import Image

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
    video_id: str
    thumbnail: str | None
    url: str
    duration: int
    view_count: int
    like_count: int
    uploader: str
    height: int
    width: int


class YTDL:
    __slots__ = ("download", "file_path", "options")

    def __init__(self, download: bool) -> None:
        self.options = {"quiet": True, "no_warnings": True, "format": "best"}
        self.download: bool = download
        self.file_path: str | None = None

    async def process_url(self, url: str) -> dict[str, Any] | None:
        loop = asyncio.get_event_loop()
        try:
            self.file_path = None
            with yt_dlp.YoutubeDL(self.options) as ydl:
                info = await loop.run_in_executor(None, ydl.extract_info, url, self.download)
                if self.download:
                    self.file_path = Path(ydl.prepare_filename(info)).as_posix()
                return info
        except yt_dlp.DownloadError as err:
            log.exception("Error downloading content from '%s'", url)
            raise DownloadError(err.msg) from err

    async def _download(self, url: str, options: dict[str, Any]) -> VideoInfo:
        self.options.update(options)
        self.download = True
        info = await self.process_url(url)
        if not info or not self.file_path:
            msg = "Failed to download content!"
            raise DownloadError(msg)

        log.debug("Download completed for %s, saved to %s", url, self.file_path)

        return await self.generate_videoinfo(info)

    async def get_info(self, url: str, options: dict[str, Any]) -> VideoInfo:
        self.options.update(options)
        self.download = False
        info = await self.process_url(url)
        if not info:
            msg = "Failed to extract video info!"
            raise InfoExtractionError(msg)

        log.debug("Information extracted for %s", url)
        return await self.generate_videoinfo(info)

    @staticmethod
    def resize_thumbnail(thumbnail_path: str) -> None:
        with Image.open(thumbnail_path) as img:
            img = img.convert("RGB")

            max_size = 320
            width, height = img.size
            if width > height:
                new_width = max_size
                new_height = int(max_size * height / width)
            else:
                new_height = max_size
                new_width = int(max_size * width / height)
            img = img.resize((new_width, new_height))

            temp_path = thumbnail_path + ".temp.jpeg"
            img.save(temp_path, "JPEG", quality=95)

            if Path(temp_path).stat().st_size < 200 * 1024:
                Path(temp_path).rename(thumbnail_path)
            else:
                img.save(thumbnail_path, "JPEG", quality=85)

    async def generate_videoinfo(self, info: dict[str, Any]) -> VideoInfo:
        loop = asyncio.get_event_loop()
        thumbnail = None
        if self.download and self.file_path:
            thumbnail = Path(self.file_path).with_suffix(".jpeg").as_posix()
            await loop.run_in_executor(None, self.resize_thumbnail, thumbnail)

        return VideoInfo(
            title=info.get("title", ""),
            video_id=info.get("id", ""),
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
    __slots__ = ("audio_options", "file_path", "thumbnail_path", "video_options")

    def __init__(self) -> None:
        self.thumbnail_path: str | None = None
        self.file_path: str | None = None
        timestamp = datetime.now(UTC).strftime("%d%m%Y%H%M%S")

        self.audio_options = {
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
            "outtmpl": f"downloads/%(title)s [%(id)s] {timestamp}.%(ext)s",
            "format": "bestaudio[filesize<=300M][ext=m4a]",
        }
        self.video_options = {
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
            "outtmpl": f"downloads/%(title)s [%(id)s] {timestamp}.%(ext)s",
            "format": "mergeall[filesize<=300M][height<=1080][ext=mp4]",
        }

    @staticmethod
    async def get_video_info(url: str) -> VideoInfo:
        ytdl = YTDL(download=False)
        return await ytdl.get_info(url, {})

    async def download(self, url: str, options: dict[str, Any]) -> VideoInfo:
        ytdl = YTDL(download=True)
        info = await ytdl._download(url, options)

        self.thumbnail_path = info.thumbnail
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
                log.debug("Removed file %s", path)

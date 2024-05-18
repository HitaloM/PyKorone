# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import io
from collections.abc import Generator
from dataclasses import dataclass
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


class FileSizeError(YTDLError):
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
    __slots__ = ("options",)

    def __init__(self, options: dict[str, Any]) -> None:
        self.options = options

    async def process_url(self, url: str, download: bool) -> dict[str, Any] | None:
        try:
            with yt_dlp.YoutubeDL(self.options) as ydl:
                return ydl.extract_info(url, download=download)
        except Exception as err:
            log.error("Error downloading content from %s: %s", url, err)
            raise YTDLError(url, "Failed to download content") from err

    async def download(self, url: str, options: dict[str, Any]) -> tuple[VideoInfo, str]:
        self.options.update(options)
        info = await self.process_url(url, download=True)
        if not info:
            raise DownloadError(url)

        file_path = yt_dlp.YoutubeDL(self.options).prepare_filename(info)
        log.debug("Download completed for %s, saved to %s", url, file_path)

        info = await self.generate_videoinfo(info)
        return info, file_path

    async def get_info(self, url: str, options: dict[str, Any]) -> VideoInfo:
        self.options.update(options)
        info = await self.process_url(url, download=False)
        if not info:
            raise InfoExtractionError(url)

        log.debug("Information extracted for %s", url)
        return await self.generate_videoinfo(info)

    @staticmethod
    async def generate_videoinfo(info: dict[str, Any]) -> VideoInfo:
        thumbnail = info.get("thumbnail")
        if not thumbnail:
            msg = "Thumbnail not found"
            raise InfoExtractionError(msg)

        httpx_timeout = httpx.Timeout(10.0, connect=5.0, read=5.0)
        async with httpx.AsyncClient(http2=True, timeout=httpx_timeout) as http:
            r = await http.get(thumbnail)
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


def format_selector(ctx, download_audio: bool = False) -> Generator[dict, None, None]:
    max_file_size = 300 * 1024 * 1024  # 300MB

    formats = ctx.get("formats")[::-1]

    if download_audio:
        best_audio = next(
            (
                f
                for f in formats
                if f["acodec"] != "none" and f["vcodec"] == "none" and f["ext"] == "m4a"
            ),
            None,
        )
        if best_audio and best_audio.get("filesize", 0) > max_file_size:
            msg = "Audio file size exceeds 300MB"
            raise FileSizeError(msg)
        if best_audio:
            yield best_audio
    else:
        best_video = next(
            f
            for f in formats
            if f["vcodec"] != "none"
            and (f.get("acodec") is None or f["acodec"] == "none")
            and f["ext"] == "mp4"
            and f.get("filesize") is not None
            and f["height"] in {144, 240, 360, 480, 720, 1080}
        )
        if best_video and best_video.get("filesize", 0) > max_file_size:
            msg = "Video file size exceeds 300MB"
            raise FileSizeError(msg)

        if best_video:
            audio_ext = {"mp4": "m4a", "webm": "webm"}.get(best_video["ext"], "m4a")
            best_audio = next(
                (
                    f
                    for f in formats
                    if f["acodec"] != "none" and f["vcodec"] == "none" and f["ext"] == audio_ext
                ),
                None,
            )
            if best_audio and best_audio.get("filesize", 0) > max_file_size:
                msg = "Audio file size exceeds 300MB"
                raise FileSizeError(msg)

            if best_audio:
                total_size = (best_video.get("filesize", 0) or 0) + (
                    best_audio.get("filesize", 0) or 0
                )
                if total_size > max_file_size:
                    msg = "Combined video and audio file size exceeds 300MB"
                    raise FileSizeError(msg)

                yield {
                    "format_id": f'{best_video["format_id"]}+{best_audio["format_id"]}',
                    "ext": best_video["ext"],
                    "requested_formats": [best_video, best_audio],
                    "protocol": f'{best_video["protocol"]}+{best_audio["protocol"]}',
                }
            else:
                yield best_video


class YtdlpManager:
    __slots__ = ("file_path", "ytdl")

    def __init__(self) -> None:
        self.ytdl = YTDL({"quiet": True, "no_warnings": True, "format": "best"})
        self.file_path: str | None = None

    async def get_video_info(self, url: str) -> VideoInfo:
        return await self.ytdl.get_info(url, {})

    async def download_video(self, url: str) -> tuple[VideoInfo, str]:
        info, file_path = await self.ytdl.download(
            url,
            {
                "format": format_selector,
                "outtmpl": "downloads/%(title)s.%(ext)s",
                "noplaylist": True,
            },
        )
        self.file_path = file_path
        return info, file_path

    async def download_audio(self, url: str) -> tuple[VideoInfo, str]:
        info, file_path = await self.ytdl.download(
            url,
            {
                "format": lambda ctx: format_selector(ctx, download_audio=True),
                "outtmpl": "downloads/%(title)s.%(ext)s",
                "noplaylist": True,
            },
        )
        self.file_path = file_path
        return info, file_path

    def clear(self) -> None:
        if self.file_path:
            file = Path(self.file_path)
            if file.exists():
                file.unlink()
                log.debug("Removed file %s", self.file_path)
            self.file_path = None

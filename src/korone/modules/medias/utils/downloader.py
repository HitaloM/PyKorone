# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio
import tempfile
from contextlib import AsyncExitStack
from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

import aiofiles
import httpx
import m3u8
from PIL import Image

from korone.modules.medias.utils.generic_headers import GENERIC_HEADER
from korone.utils.logging import logger

MIME_TYPE_TO_EXTENSION = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
    "video/mp4": "mp4",
    "video/webm": "webm",
    "video/quicktime": "mov",
    "video/x-msvideo": "avi",
    "application/vnd.apple.mpegurl": "m3u8",
}


def is_supported_mime_type(mime_type: str) -> bool:
    return mime_type in MIME_TYPE_TO_EXTENSION


def is_bsky_thumbnail(media_url: str, mime_type: str) -> bool:
    return "bsky.app" in media_url and mime_type == "application/octet-stream"


async def fetch_media_url(media_url: str) -> httpx.Response:
    async with httpx.AsyncClient(
        headers=GENERIC_HEADER, http2=True, timeout=20, follow_redirects=True, max_redirects=5
    ) as client:
        response = await client.get(media_url)
        response.raise_for_status()
        return response


def get_file_extension(mime_type: str) -> str:
    return MIME_TYPE_TO_EXTENSION.get(mime_type, "")


def convert_to_jpeg(image_data: BytesIO, file_path: Path) -> BytesIO:
    image = Image.open(image_data)
    jpeg_buffer = BytesIO()
    image.convert("RGB").save(jpeg_buffer, format="JPEG")
    jpeg_buffer.name = file_path.with_suffix(".jpeg").name
    return jpeg_buffer


async def download_segment(segment_url: str, stack: AsyncExitStack) -> Path | None:
    try:
        response = await fetch_media_url(segment_url)
        content = await response.aread()

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".ts")  # noqa: SIM115
        stack.callback(lambda: Path(temp_file.name).unlink(missing_ok=True))

        async with aiofiles.open(temp_file.name, mode="wb") as file:
            await file.write(content)

        return Path(temp_file.name)
    except Exception as error:
        await logger.aerror("[Medias/Downloader] Failed to download segment: %s", error)
        return None


async def merge_m3u8_segments(segment_files: list[Path], stack: AsyncExitStack) -> BytesIO | None:
    try:
        list_file = tempfile.NamedTemporaryFile(delete=False, suffix=".txt")  # noqa: SIM115
        stack.callback(lambda: Path(list_file.name).unlink(missing_ok=True))

        async with aiofiles.open(list_file.name, mode="w") as f:
            for segment_file in segment_files:
                await f.write(f"file '{segment_file.resolve()}'\n")

        output_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")  # noqa: SIM115
        stack.callback(lambda: Path(output_file.name).unlink(missing_ok=True))

        ffmpeg_command = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            list_file.name,
            "-c",
            "copy",
            output_file.name,
        ]

        process = await asyncio.create_subprocess_exec(
            *ffmpeg_command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            await logger.aerror(
                "[Medias/Downloader] ffmpeg failed with return code %s\nstdout: %s\nstderr: %s",
                process.returncode,
                stdout.decode(),
                stderr.decode(),
            )
            return None

        async with aiofiles.open(output_file.name, mode="rb") as f:
            merged_content = await f.read()
            merged_file = BytesIO(merged_content)
            merged_file.name = output_file.name
            return merged_file

    except Exception as error:
        await logger.aerror("[Medias/Downloader] Error merging segments: %s", error)
        return None


async def download_m3u8_playlist(media_url: str, content: bytes) -> BytesIO | None:
    playlist = m3u8.loads(content.decode("utf-8"))
    parsed_url = urlparse(media_url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}{Path(parsed_url.path).parent}"

    async with AsyncExitStack() as stack:
        try:
            segment_files = await asyncio.gather(*[
                download_segment(f"{base_url}/{segment.uri}", stack)
                for segment in playlist.segments
            ])
            valid_segment_files = [file for file in segment_files if file]
            return await merge_m3u8_segments(valid_segment_files, stack)
        except Exception as error:
            await logger.aerror("[Medias/Downloader] Error downloading M3U8 segments: %s", error)
            return None


async def download_media(media_url: str) -> BytesIO | None:
    try:
        response = await fetch_media_url(media_url)
        content_type: str = response.headers.get("content-type", "")

        if not is_bsky_thumbnail(media_url, content_type) and not is_supported_mime_type(
            content_type
        ):
            await logger.awarning("[Medias/Downloader] MIME type not supported: %s", content_type)
            return None

        raw_data = await response.aread()
        buffer = BytesIO(raw_data)
        file_path = Path(urlparse(media_url).path)
        buffer.name = file_path.name

        if b"#EXTM3U" in raw_data:
            return await download_m3u8_playlist(media_url, raw_data)

        if file_path.suffix.lower() in {".webp", ".heic"}:
            return convert_to_jpeg(buffer, file_path)

        return buffer

    except httpx.HTTPStatusError as error:
        await logger.aerror("[Medias/Downloader] HTTP error: %s", error)
        return None
    except Exception as error:
        await logger.aerror("[Medias/Downloader] Error downloading media: %s", error)
        return None

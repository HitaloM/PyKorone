# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import asyncio
import shutil
import tempfile
from contextlib import AsyncExitStack
from io import BytesIO
from pathlib import Path
from urllib.parse import urljoin, urlparse

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
MAX_FILE_SIZE: int = 10 * 1024 * 1024  # 10 MB
MAX_DIMENSION: int = 10000
MAX_RATIO: int = 20


def is_supported_mime_type(mime_type: str) -> bool:
    return mime_type in MIME_TYPE_TO_EXTENSION


def is_bsky_thumbnail(media_url: str, mime_type: str) -> bool:
    return "bsky.app" in media_url and mime_type == "application/octet-stream"


async def fetch_media_url(client: httpx.AsyncClient, media_url: str) -> httpx.Response:
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


async def download_segment(
    session: httpx.AsyncClient, segment_url: str, temp_dir: Path
) -> Path | None:
    try:
        response = await session.get(segment_url)
        response.raise_for_status()
        content = response.content

        segment_name = Path(urlparse(segment_url).path).name
        segment_path = temp_dir / segment_name

        async with aiofiles.open(segment_path, mode="wb") as file:
            await file.write(content)

        return segment_path
    except Exception as error:
        await logger.aerror("[Medias/Downloader] Failed to download segment: %s", error)
        return None


async def merge_m3u8_segments(segment_files: list[Path], output_path: Path) -> bool:
    try:
        segments_list_path = output_path.parent / "segments.txt"
        async with aiofiles.open(segments_list_path, mode="w") as f:
            for segment_file in segment_files:
                await f.write(f"file '{segment_file.resolve()}'\n")

        ffmpeg_command = [
            "ffmpeg",
            "-y",
            "-f",
            "concat",
            "-safe",
            "0",
            "-i",
            str(segments_list_path),
            "-c",
            "copy",
            str(output_path),
        ]

        process = await asyncio.create_subprocess_exec(
            *ffmpeg_command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await process.communicate()

        if process.returncode != 0:
            await logger.aerror(
                "[Medias/Downloader] ffmpeg failed with return code %s\nstdout: %s\nstderr: %s",
                process.returncode,
                stdout.decode(),
                stderr.decode(),
            )
            return False

        return True

    except Exception as error:
        await logger.aerror("[Medias/Downloader] Error merging segments: %s", error)
        return False


async def download_m3u8_playlist(media_url: str, content: bytes) -> BytesIO | None:
    playlist = m3u8.loads(content.decode("utf-8"))
    base_url = media_url.rsplit("/", 1)[0]

    async with AsyncExitStack() as stack:
        temp_dir = Path(tempfile.mkdtemp())

        stack.push_async_callback(
            lambda: asyncio.to_thread(shutil.rmtree, temp_dir, ignore_errors=True)
        )

        async with httpx.AsyncClient(
            headers=GENERIC_HEADER, http2=True, timeout=20, follow_redirects=True, max_redirects=5
        ) as session:
            download_tasks = [
                download_segment(session, urljoin(base_url + "/", segment.uri), temp_dir)
                for segment in playlist.segments
            ]
            segment_files = await asyncio.gather(*download_tasks)
            segment_files = [sf for sf in segment_files if sf is not None]

        if not segment_files:
            await logger.aerror("[Medias/Downloader] No segments were downloaded.")
            return None

        merged_output_path = temp_dir / "merged_video.mp4"
        merge_success = await merge_m3u8_segments(segment_files, merged_output_path)

        if not merge_success:
            return None

        async with aiofiles.open(merged_output_path, mode="rb") as f:
            merged_content = await f.read()
            merged_file = BytesIO(merged_content)
            merged_file.name = "downloaded_media.mp4"
            return merged_file


def resize_image(image: Image.Image) -> BytesIO:
    width, height = image.size
    ratio = width / height

    if ratio > MAX_RATIO:
        if width > height:
            width = MAX_RATIO * height
        else:
            height = MAX_RATIO * width

    if width + height > MAX_DIMENSION:
        scale = MAX_DIMENSION / (width + height)
        width = int(width * scale)
        height = int(height * scale)

    width = max(10, min(width, MAX_DIMENSION))
    height = max(10, min(height, MAX_DIMENSION))

    resized_image = image.resize((width, height), Image.Resampling.LANCZOS)
    buffer = BytesIO()
    resized_image.save(buffer, format="JPEG")
    buffer.seek(0)

    if buffer.tell() > MAX_FILE_SIZE:
        quality = 95
        while buffer.tell() > MAX_FILE_SIZE and quality > 10:
            buffer = BytesIO()
            resized_image.save(buffer, format="JPEG", quality=quality)
            buffer.seek(0)
            quality -= 5

    return buffer


def process_image(buffer: BytesIO, file_path: Path) -> BytesIO:
    image = Image.open(buffer)
    buffer.seek(0, 2)  # Move to the end of the buffer

    if (
        buffer.tell() > MAX_FILE_SIZE
        or image.width + image.height > MAX_DIMENSION
        or image.width / image.height > MAX_RATIO
    ):
        buffer = resize_image(image)
        buffer.name = file_path.with_suffix(".jpeg").name

    return buffer


async def download_media(media_url: str) -> BytesIO | None:
    try:
        async with httpx.AsyncClient(
            headers=GENERIC_HEADER, http2=True, timeout=20, follow_redirects=True, max_redirects=5
        ) as client:
            response = await fetch_media_url(client, media_url)
        content_type: str = response.headers.get("content-type", "")

        if not is_bsky_thumbnail(media_url, content_type) and not is_supported_mime_type(
            content_type
        ):
            await logger.awarning("[Medias/Downloader] MIME type not supported: %s", content_type)
            return None

        raw_data = response.content
        buffer = BytesIO(raw_data)
        file_path = Path(urlparse(media_url).path)

        if not file_path.name:
            extension = get_file_extension(content_type)
            buffer.name = f"downloaded_media.{extension}"
        else:
            buffer.name = file_path.name
            if not file_path.suffix:
                extension = get_file_extension(content_type)
                buffer.name = f"{buffer.name}.{extension}"

        if b"#EXTM3U" in raw_data:
            return await download_m3u8_playlist(media_url, raw_data)

        if file_path.suffix.lower() in {".webp", ".heic"}:
            return convert_to_jpeg(buffer, file_path)

        if content_type.startswith("image/"):
            return process_image(buffer, file_path)

        return buffer

    except httpx.HTTPStatusError as error:
        await logger.aerror("[Medias/Downloader] HTTP error: %s", error)
        return None
    except Exception as error:
        await logger.aerror("[Medias/Downloader] Error downloading media: %s", error)
        return None

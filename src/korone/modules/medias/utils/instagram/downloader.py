# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import io
from pathlib import Path
from urllib.parse import urlparse

import httpx
from PIL import Image

mime_extensions = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
    "video/mp4": "mp4",
    "video/webm": "webm",
    "video/quicktime": "mov",
    "video/x-msvideo": "avi",
}


async def fetch_media(media: str) -> httpx.Response:
    async with httpx.AsyncClient(http2=True, timeout=10) as client:
        response = await client.get(media)
        response.raise_for_status()
        return response


def get_extension(content_type: str) -> str:
    return mime_extensions.get(content_type, "")


def convert_image_to_jpeg(file: io.BytesIO, file_path: Path) -> io.BytesIO:
    image = Image.open(file)
    file_jpg = io.BytesIO()
    image.convert("RGB").save(file_jpg, format="JPEG")
    file_jpg.name = file_path.with_suffix(".jpeg").name
    return file_jpg


async def downloader(media: str) -> io.BytesIO | None:
    try:
        response = await fetch_media(media)
        content_type = response.headers.get("content-type")
        extension = get_extension(content_type)
        if not extension:
            return None

        content = await response.aread()
        file = io.BytesIO(content)
        file_path = Path(urlparse(media).path)
        file.name = file_path.name

        if content_type.startswith("video"):
            return file

        if file_path.suffix.lower() in {".webp", ".heic"}:
            return convert_image_to_jpeg(file, file_path)

        return file

    except httpx.HTTPStatusError:
        return None
    except Exception:
        return None

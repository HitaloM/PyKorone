# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from io import BytesIO
from pathlib import Path
from urllib.parse import urlparse

import httpx
from PIL import Image

MIME_EXTENSIONS = {
    "image/jpeg": "jpg",
    "image/png": "png",
    "image/gif": "gif",
    "image/webp": "webp",
    "video/mp4": "mp4",
    "video/webm": "webm",
    "video/quicktime": "mov",
    "video/x-msvideo": "avi",
}


def is_supported_mime_type(content_type: str) -> bool:
    return content_type in MIME_EXTENSIONS


async def fetch_media(media_url: str) -> httpx.Response:
    async with httpx.AsyncClient(http2=True, timeout=10) as client:
        response = await client.get(media_url)
        response.raise_for_status()
        return response


def get_extension(content_type: str) -> str:
    return MIME_EXTENSIONS.get(content_type, "")


def convert_image_to_jpeg(file: BytesIO, file_path: Path) -> BytesIO:
    image = Image.open(file)
    file_jpg = BytesIO()
    image.convert("RGB").save(file_jpg, format="JPEG")
    file_jpg.name = file_path.with_suffix(".jpeg").name
    return file_jpg


async def download_media(media_url: str) -> BytesIO | None:
    try:
        response = await fetch_media(media_url)
        content_type = response.headers.get("content-type", "")

        if not is_supported_mime_type(content_type):
            return None

        content = await response.aread()
        file = BytesIO(content)
        file_path = Path(urlparse(media_url).path)
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

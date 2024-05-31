# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import io
import mimetypes
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlparse

import httpx
from PIL import Image

from korone import cache
from korone.modules.media_dl.utils.instagram.scraper import TIMEOUT


@cache(ttl=timedelta(days=1))
async def url_to_binary_io(url: str) -> io.BytesIO:
    async with httpx.AsyncClient(timeout=TIMEOUT, http2=True) as session:
        mime_type = mimetypes.guess_type(url)[0]
        proxy_url = f"https://envoy.lol/{url}"

        response = await session.get(
            proxy_url if mime_type and mime_type.startswith("video") else url
        )
        content = await response.aread()
        file = io.BytesIO(content)
        file_path = Path(urlparse(url).path)
        file.name = file_path.name

        if mime_type and mime_type.startswith("video"):
            return file

        if file_path.suffix.lower() in {".webp", ".heic"}:
            image = Image.open(file)
            file_jpg = io.BytesIO()
            image.convert("RGB").save(file_jpg, format="JPEG")
            file_jpg.name = file_path.with_suffix(".jpeg").name
            return file_jpg

        return file


def mediaid_to_code(media_id: int) -> str:
    alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
    if media_id == 0:
        return alphabet[0]

    code = []
    base = len(alphabet)

    while media_id:
        media_id, rem = divmod(media_id, base)
        code.append(alphabet[rem])

    return "".join(reversed(code))

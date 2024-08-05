# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import random
import string
from datetime import timedelta
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

import httpx
from PIL import Image
from pydantic import HttpUrl

from korone import cache


def resize_thumbnail(thumbnail_path: str | BytesIO | BinaryIO) -> None:
    with Image.open(thumbnail_path) as img:
        original_width, original_height = img.size
        aspect_ratio = original_width / original_height
        larger_dimension = max(original_width, original_height)
        new_width = (
            larger_dimension
            if original_width == larger_dimension
            else int(larger_dimension * aspect_ratio)
        )
        new_height = (
            larger_dimension
            if original_width != larger_dimension
            else int(larger_dimension / aspect_ratio)
        )
        resized_img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)

        if isinstance(thumbnail_path, str):
            temp_path = f"{thumbnail_path}.temp.jpeg"
            resized_img.save(temp_path, "JPEG", quality=95)

            if Path(temp_path).stat().st_size < 200 * 1024:
                Path(temp_path).rename(thumbnail_path)
            else:
                resized_img.save(thumbnail_path, "JPEG", quality=85)
                Path(temp_path).unlink(missing_ok=True)
        else:
            thumbnail_path.seek(0)
            resized_img.save(thumbnail_path, "JPEG", quality=85)
            thumbnail_path.truncate()


@cache(ttl=timedelta(weeks=1))
async def url_to_bytes_io(url: HttpUrl, *, video: bool) -> BytesIO:
    try:
        async with httpx.AsyncClient(http2=True) as client:
            response = await client.get(str(url))
            response.raise_for_status()
            content = await response.aread()
    except httpx.HTTPError:
        raise

    file = BytesIO(content)
    random_suffix = "".join(random.choices(string.ascii_letters + string.digits, k=8))
    if video and url.path and Path(url.path).suffix == ".gif":
        file.name = f"{url.host}-{random_suffix}.gif"
    else:
        file.name = f"{url.host}-{random_suffix}.{"mp4" if video else "jpeg"}"
    return file

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from contextlib import suppress
from io import BytesIO
from pathlib import Path
from typing import BinaryIO

from PIL import Image


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
            temp_path = Path(f"{thumbnail_path}.temp.jpeg")
            resized_img.save(temp_path, "JPEG", quality=95)

            if temp_path.stat().st_size < 200 * 1024:
                temp_path.replace(thumbnail_path)
            else:
                resized_img.save(thumbnail_path, "JPEG", quality=85)
                with suppress(FileNotFoundError):
                    temp_path.unlink()
        else:
            thumbnail_path.seek(0)
            resized_img.save(thumbnail_path, "JPEG", quality=85)
            thumbnail_path.truncate()
            thumbnail_path.seek(0)

        resized_img.close()

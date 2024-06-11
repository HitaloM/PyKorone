# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import random
import string
from pathlib import Path
from typing import BinaryIO

from PIL import Image

from korone import app_dir


def generate_random_file_path(prefix: str, extension: str = ".mp4") -> Path:
    output_path = Path(app_dir / "downloads")
    output_path.mkdir(exist_ok=True, parents=True)

    random_suffix = "".join(random.choices(string.ascii_letters + string.digits, k=8))
    return output_path / f"{prefix}{random_suffix}{extension}"


def resize_thumbnail(thumbnail_path: str | BinaryIO) -> None:
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
            temp_path = thumbnail_path + ".temp.jpeg"
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

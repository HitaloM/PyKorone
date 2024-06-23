# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio
import random
import string
from pathlib import Path

from PIL import Image

from korone import app_dir


def resize_image(image_path: str) -> str:
    with Image.open(image_path) as img:
        img.thumbnail((512, 512), Image.Resampling.LANCZOS)
        new_path = generate_random_file_path("resized_", ".webp").as_posix()
        img.save(new_path, "WEBP")
    return new_path


async def resize_video(video_path: str) -> str:
    new_path = generate_random_file_path("resized_", ".webm").as_posix()
    command = [
        "ffmpeg",
        "-i",
        video_path,
        "-vf",
        "scale=512:512",
        "-c:v",
        "libvpx-vp9",
        "-b:v",
        "256k",
        "-r",
        "30",
        "-t",
        "3",
        "-an",
        new_path,
    ]
    process = await asyncio.create_subprocess_exec(*command)
    await process.wait()
    return new_path


def generate_random_file_path(prefix: str, extension: str) -> Path:
    output_path = Path(app_dir / "downloads")
    output_path.mkdir(exist_ok=True, parents=True)

    random_suffix = "".join(random.choices(string.ascii_letters + string.digits, k=8))
    return output_path / f"{prefix}{random_suffix}{extension}"

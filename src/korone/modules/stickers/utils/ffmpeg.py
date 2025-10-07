# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import random
import string
from pathlib import Path
from subprocess import PIPE, STDOUT

import anyio
from PIL import Image

from korone import constants


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
    await anyio.run_process(command, check=False)
    return new_path


def generate_random_file_path(prefix: str, extension: str) -> Path:
    output_path = Path(constants.BOT_ROOT_PATH / "downloads")
    output_path.mkdir(exist_ok=True, parents=True)

    random_suffix = "".join(random.choices(string.ascii_letters + string.digits, k=8))
    return output_path / f"{prefix}{random_suffix}{extension}"


async def run_ffprobe_command(file_path: str) -> str | None:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "format=duration",
        "-of",
        "default=noprint_wrappers=1:nokey=1",
        file_path,
    ]
    result = await anyio.run_process(
        command,
        stdout=PIPE,
        stderr=STDOUT,
        check=False,
    )

    return result.stdout.decode() if result.stdout else None


async def ffprobe(file_path: str) -> float | None:
    if raw_output := await run_ffprobe_command(file_path):
        try:
            return float(raw_output.strip())
        except ValueError:
            return None
    return None

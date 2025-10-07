# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import random
import string
from subprocess import PIPE, STDOUT

from anyio import Path, run_process, to_thread
from PIL import Image

from korone import constants

DOWNLOADS_PATH: Path = Path(constants.BOT_ROOT_PATH / "downloads")


async def resize_image(image_path: str) -> str:
    output_path = (await generate_random_file_path("resized_", ".webp")).as_posix()

    def _resize() -> str:
        with Image.open(image_path) as img:
            img.thumbnail((512, 512), Image.Resampling.LANCZOS)
            img.save(output_path, "WEBP")
        return output_path

    return await to_thread.run_sync(_resize)


async def resize_video(video_path: str) -> str:
    new_path = (await generate_random_file_path("resized_", ".webm")).as_posix()
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
    result = await run_process(command, check=False)
    if result.returncode != 0:
        msg = "ffmpeg failed to resize the provided video"
        raise RuntimeError(msg)
    return new_path


async def generate_random_file_path(prefix: str, extension: str) -> Path:
    await DOWNLOADS_PATH.mkdir(parents=True, exist_ok=True)
    random_suffix = "".join(random.choices(string.ascii_letters + string.digits, k=8))
    return DOWNLOADS_PATH / f"{prefix}{random_suffix}{extension}"


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
    result = await run_process(
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

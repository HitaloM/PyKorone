# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio
from pathlib import Path

import aiofiles
import orjson

from korone.modules.media_dl.utils.files import generate_random_file_path


async def save_binary_io(binary_io) -> str:
    output_file_path = generate_random_file_path("tweet_original_video-")

    try:
        async with aiofiles.open(output_file_path, "wb") as file:
            await file.write(binary_io.read())
    except OSError as e:
        msg = f"Failed to save binary IO: {e}"
        raise RuntimeError(msg) from e

    return output_file_path.as_posix()


async def video_has_audio(video_path: str) -> bool:
    command = ["ffprobe", "-v", "quiet", "-print_format", "json", "-show_streams", video_path]

    try:
        process = await asyncio.create_subprocess_exec(
            *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
        )
        stdout, _ = await process.communicate()
        output = orjson.loads(stdout)
    except (OSError, ValueError) as e:
        msg = f"Failed to check video audio: {e}"
        raise RuntimeError(msg) from e

    return any(stream["codec_type"] == "audio" for stream in output["streams"])


async def add_silent_audio(video_path: str) -> str:
    output_file_path = generate_random_file_path("tweet_converted_video-").as_posix()
    command = [
        "ffmpeg",
        "-i",
        video_path,
        "-f",
        "lavfi",
        "-i",
        "anullsrc",
        "-shortest",
        "-c:v",
        "copy",
        "-c:a",
        "aac",
        output_file_path,
    ]

    try:
        process = await asyncio.create_subprocess_exec(
            *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.STDOUT
        )
        await process.communicate()
    except OSError as e:
        msg = f"Failed to add silent audio: {e}"
        raise RuntimeError(msg) from e

    return output_file_path


async def delete_files(files: list[str]) -> None:
    loop = asyncio.get_event_loop()
    await asyncio.gather(
        *(
            loop.run_in_executor(None, lambda file: Path(file).unlink(missing_ok=True), file)
            for file in files
        )
    )

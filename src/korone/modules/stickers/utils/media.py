from __future__ import annotations

import asyncio
import json
import math
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from aiogram.types import FSInputFile, InputSticker
from PIL import Image

from korone.modules.utils_.telegram_file import download_telegram_file
from korone.utils.i18n import gettext as _

from .constants import MAX_STICKER_SIDE, MAX_VIDEO_SECONDS, MAX_VIDEO_SIZE_BYTES, VIDEO_EXTENSIONS
from .errors import StickerPrepareError

if TYPE_CHECKING:
    from aiogram import Bot
    from aiogram.types import Message, Sticker


@dataclass(slots=True, frozen=True)
class VideoMeta:
    width: int
    height: int
    duration: float
    fps: float


def infer_extension(file_name: str | None, mime_type: str | None, *, default: str) -> str:
    if file_name and (suffix := Path(file_name).suffix.lower()):
        return suffix

    if mime_type:
        subtype = mime_type.lower().split("/", maxsplit=1)[-1].split(";", maxsplit=1)[0]
        if "tgsticker" in subtype:
            return ".tgs"

        filtered = "".join(ch for ch in subtype if ch.isalnum())
        if filtered:
            return f".{filtered[:10]}"

    return default


def suffix_from_sticker(sticker: Sticker) -> str:
    if sticker.is_animated:
        return ".tgs"
    if sticker.is_video:
        return ".webm"
    return ".webp"


def extract_reply_media(message: Message) -> tuple[str, str, str | None]:
    if not (reply := message.reply_to_message):
        msg = "Message is not a reply"
        raise ValueError(msg)

    if sticker := reply.sticker:
        return sticker.file_id, suffix_from_sticker(sticker), sticker.emoji

    if reply.photo:
        return reply.photo[-1].file_id, ".jpg", None

    if animation := reply.animation:
        return animation.file_id, infer_extension(animation.file_name, animation.mime_type, default=".mp4"), None

    if video := reply.video:
        return video.file_id, infer_extension(video.file_name, video.mime_type, default=".mp4"), None

    if document := reply.document:
        return document.file_id, infer_extension(document.file_name, document.mime_type, default=".bin"), None

    msg = "Reply does not contain supported media"
    raise ValueError(msg)


async def download_file(bot: Bot, file_id: str, destination: Path) -> None:
    await download_telegram_file(bot=bot, file_id=file_id, destination=destination)


async def prepare_sticker_file(source_path: Path) -> tuple[Path, str]:
    suffix = source_path.suffix.lower()

    if suffix == ".tgs":
        return source_path, "animated"

    if suffix == ".webm":
        return source_path, "video"

    if suffix in VIDEO_EXTENSIONS:
        output = source_path.with_suffix(".webm")
        await convert_video_for_sticker(source_path, output)
        return output, "video"

    output = source_path.with_suffix(".png")
    await convert_image_for_sticker(source_path, output)
    return output, "static"


def create_input_sticker(path: Path, *, sticker_format: str, emoji: str) -> InputSticker:
    return InputSticker(sticker=FSInputFile(path), format=sticker_format, emoji_list=[emoji])


async def convert_image_for_sticker(source_path: Path, output_path: Path) -> None:
    try:
        await asyncio.to_thread(_convert_image_for_sticker_sync, source_path, output_path)
    except OSError as exc:
        raise StickerPrepareError(_("Could not process this file as an image sticker.")) from exc


def _convert_image_for_sticker_sync(source_path: Path, output_path: Path) -> None:
    with Image.open(source_path) as img:
        img.load()
        converted = img.convert("RGBA")

        width, height = converted.size
        if width <= 0 or height <= 0:
            msg = "Invalid image dimensions"
            raise OSError(msg)

        scale = MAX_STICKER_SIDE / max(width, height)
        new_width = max(1, math.floor(width * scale))
        new_height = max(1, math.floor(height * scale))

        if (new_width, new_height) != converted.size:
            converted = converted.resize((new_width, new_height), Image.Resampling.LANCZOS)

        converted.save(output_path, format="PNG")
        converted.close()


async def convert_video_for_sticker(source_path: Path, output_path: Path) -> None:
    if not is_ffmpeg_available():
        raise StickerPrepareError(_("Video conversion is unavailable because ffmpeg/ffprobe are not installed."))

    video_meta = await probe_video(source_path)
    if video_meta.duration > MAX_VIDEO_SECONDS:
        raise StickerPrepareError(
            _("Video is too long ({duration:.2f}s). Maximum allowed duration is 3 seconds.").format(
                duration=video_meta.duration
            )
        )

    scale_width, scale_height = (512, -2) if video_meta.width >= video_meta.height else (-2, 512)
    command = [
        "ffmpeg",
        "-y",
        "-i",
        str(source_path),
        "-t",
        str(MAX_VIDEO_SECONDS),
        "-vf",
        f"scale={scale_width}:{scale_height}",
        "-an",
        "-c:v",
        "libvpx-vp9",
        "-b:v",
        "0",
        "-crf",
        "36",
    ]

    if video_meta.fps > 30:
        command.extend(["-r", "30"])

    command.append(str(output_path))
    status, _stdout, _stderr = await run_subprocess(command)
    output_exists = await asyncio.to_thread(path_exists, output_path)
    if status != 0 or not output_exists:
        raise StickerPrepareError(_("Could not convert this video to a valid sticker."))

    size_bytes = await asyncio.to_thread(path_size, output_path)
    if size_bytes > MAX_VIDEO_SIZE_BYTES:
        raise StickerPrepareError(
            _("Converted video is too large ({size_kb:.1f} KB). Maximum allowed size is 256 KB.").format(
                size_kb=size_bytes / 1000
            )
        )


def is_ffmpeg_available() -> bool:
    return bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))


async def probe_video(path: Path) -> VideoMeta:
    command = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-show_entries",
        "stream=width,height,avg_frame_rate:format=duration",
        "-of",
        "json",
        str(path),
    ]
    status, stdout, _stderr = await run_subprocess(command)
    if status != 0:
        raise StickerPrepareError(_("Could not inspect video metadata."))

    try:
        payload = json.loads(stdout)
        stream = payload["streams"][0]
        width = int(stream["width"])
        height = int(stream["height"])
        fps = parse_fps(str(stream.get("avg_frame_rate", "0")))
        duration = float(payload["format"]["duration"])
    except (ValueError, TypeError, KeyError, IndexError, json.JSONDecodeError) as exc:
        raise StickerPrepareError(_("Could not parse video metadata.")) from exc

    if width <= 0 or height <= 0 or duration <= 0:
        raise StickerPrepareError(_("Video metadata is invalid."))

    return VideoMeta(width=width, height=height, duration=duration, fps=fps)


def parse_fps(raw_value: str) -> float:
    if "/" in raw_value:
        numerator, denominator = raw_value.split("/", maxsplit=1)
        try:
            den = float(denominator)
            if den == 0:
                return 0.0
            return float(numerator) / den
        except ValueError:
            return 0.0

    try:
        return float(raw_value)
    except ValueError:
        return 0.0


def path_exists(path: Path) -> bool:
    return path.exists()


def path_size(path: Path) -> int:
    return path.stat().st_size


async def run_subprocess(command: list[str]) -> tuple[int, str, str]:
    process = await asyncio.create_subprocess_exec(
        *command, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    stdout, stderr = await process.communicate()
    returncode = process.returncode if process.returncode is not None else 1
    return returncode, stdout.decode("utf-8", errors="replace"), stderr.decode("utf-8", errors="replace")

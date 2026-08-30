import asyncio
from dataclasses import replace
from io import BytesIO
from pathlib import Path
from typing import Final

from aiogram.types import BufferedInputFile
from PIL import Image, ImageOps

from korone.constants import (
    TELEGRAM_PHOTO_MAX_ASPECT_RATIO,
    TELEGRAM_PHOTO_MAX_DIMENSIONS_SUM,
    TELEGRAM_PHOTO_MAX_FILE_SIZE_BYTES,
)
from korone.logger import get_logger
from korone.modules.medias.models import MediaKind, PreparedMedia

DEFAULT_QUALITY_STEPS: Final[tuple[int, ...]] = (88, 76, 64, 52, 40)
DEFAULT_MAX_PASSES: Final[int] = 6
logger = get_logger(__name__)


def _target_photo_dimensions(
    width: int, height: int, *, max_dimensions_sum: int, max_aspect_ratio: int
) -> tuple[int, int]:
    if width < 1 or height < 1:
        return width, height

    if width >= height:
        height = max(height, 1, (width + max_aspect_ratio - 1) // max_aspect_ratio)
    else:
        width = max(width, 1, (height + max_aspect_ratio - 1) // max_aspect_ratio)

    dimensions_sum = width + height
    if dimensions_sum <= max_dimensions_sum:
        return width, height

    scale = max_dimensions_sum / dimensions_sum
    width = max(1, int(width * scale))
    height = max(1, int(height * scale))

    if width >= height:
        height = max(height, 1, (width + max_aspect_ratio - 1) // max_aspect_ratio)
        if width + height > max_dimensions_sum:
            width = max(1, max_dimensions_sum - height)
    else:
        width = max(width, 1, (height + max_aspect_ratio - 1) // max_aspect_ratio)
        if width + height > max_dimensions_sum:
            height = max(1, max_dimensions_sum - width)

    return width, height


def _constrain_photo_dimensions(image: Image.Image, *, max_dimensions_sum: int, max_aspect_ratio: int) -> Image.Image:
    width, height = image.size
    target_width, target_height = _target_photo_dimensions(
        width, height, max_dimensions_sum=max_dimensions_sum, max_aspect_ratio=max_aspect_ratio
    )
    if target_width == width and target_height == height:
        return image

    constrained = image

    if target_width > width or target_height > height:
        expanded_width = max(width, target_width)
        expanded_height = max(height, target_height)
        expanded = Image.new("RGB", (expanded_width, expanded_height), "white")
        offset_x = (expanded_width - width) // 2
        offset_y = (expanded_height - height) // 2
        expanded.paste(constrained, (offset_x, offset_y))
        constrained = expanded
        width, height = constrained.size

    if width != target_width or height != target_height:
        resized = constrained.resize((target_width, target_height), Image.Resampling.LANCZOS)
        if constrained is not image:
            constrained.close()
        constrained = resized

    return constrained


def photo_payload_needs_resize(payload: bytes, *, max_dimensions_sum: int, max_aspect_ratio: int) -> bool:
    try:
        with Image.open(BytesIO(payload)) as source_image:
            base = ImageOps.exif_transpose(source_image)
            try:
                width, height = base.size
                if width < 1 or height < 1:
                    return True

                target_width, target_height = _target_photo_dimensions(
                    width, height, max_dimensions_sum=max_dimensions_sum, max_aspect_ratio=max_aspect_ratio
                )
                return (target_width, target_height) != (width, height)
            finally:
                if base is not source_image:
                    base.close()
    except OSError, ValueError:
        return True


def _encode_candidate_jpeg(
    image: Image.Image, *, safe_limit_bytes: int, quality_steps: tuple[int, ...], best: bytes | None
) -> tuple[bytes | None, bytes | None, bytes | None]:
    smallest_for_pass: bytes | None = None

    for quality in quality_steps:
        buffer = BytesIO()
        image.save(buffer, format="JPEG", quality=quality, optimize=False, progressive=False)
        encoded = buffer.getvalue()

        if best is None or len(encoded) < len(best):
            best = encoded
        if smallest_for_pass is None or len(encoded) < len(smallest_for_pass):
            smallest_for_pass = encoded
        if len(encoded) <= safe_limit_bytes:
            return encoded, smallest_for_pass, best

    return None, smallest_for_pass, best


def _normalized_rgb_image(source_image: Image.Image) -> Image.Image:
    transposed = ImageOps.exif_transpose(source_image)
    try:
        if transposed.mode == "RGB":
            return transposed.copy()
        if transposed.mode == "L":
            return transposed.convert("RGB")

        with transposed.convert("RGBA") as rgba, Image.new("RGBA", rgba.size, "white") as background:
            background.alpha_composite(rgba)
            return background.convert("RGB")
    finally:
        if transposed is not source_image:
            transposed.close()


def _compress_image_to_limit(
    image: Image.Image, *, safe_limit_bytes: int, quality_steps: tuple[int, ...], max_passes: int
) -> bytes | None:
    best: bytes | None = None
    base_width, base_height = image.size
    if base_width < 1 or base_height < 1:
        return None

    width, height = base_width, base_height
    for _ in range(max_passes):
        candidate_image = (
            image
            if (width, height) == (base_width, base_height)
            else image.resize((width, height), Image.Resampling.LANCZOS)
        )
        try:
            encoded, smallest_for_pass, best = _encode_candidate_jpeg(
                candidate_image, safe_limit_bytes=safe_limit_bytes, quality_steps=quality_steps, best=best
            )
        finally:
            if candidate_image is not image:
                candidate_image.close()

        if encoded is not None:
            return encoded
        if not smallest_for_pass:
            break

        ratio = safe_limit_bytes / len(smallest_for_pass)
        if ratio >= 1:
            break

        shrink = max(0.55, min(0.9, (ratio**0.5) * 0.97))
        next_size = max(1, int(width * shrink)), max(1, int(height * shrink))
        if next_size == (width, height):
            next_size = max(1, int(width * 0.9)), max(1, int(height * 0.9))
        width, height = next_size

    return best if best and len(best) <= safe_limit_bytes else None


def compress_photo_payload_to_safe_jpeg(
    payload: bytes,
    *,
    safe_limit_bytes: int,
    max_dimensions_sum: int,
    max_aspect_ratio: int,
    quality_steps: tuple[int, ...] = DEFAULT_QUALITY_STEPS,
    max_passes: int = DEFAULT_MAX_PASSES,
) -> bytes | None:
    with Image.open(BytesIO(payload)) as source_image:
        base = _normalized_rgb_image(source_image)
        try:
            constrained = _constrain_photo_dimensions(
                base, max_dimensions_sum=max_dimensions_sum, max_aspect_ratio=max_aspect_ratio
            )
            try:
                return _compress_image_to_limit(
                    constrained, safe_limit_bytes=safe_limit_bytes, quality_steps=quality_steps, max_passes=max_passes
                )
            finally:
                if constrained is not base:
                    constrained.close()
        finally:
            base.close()


class PhotoProcessor:
    __slots__ = ("_slots",)

    SAFE_LIMIT_BYTES = TELEGRAM_PHOTO_MAX_FILE_SIZE_BYTES - 32 * 1024
    MAX_DIMENSIONS_SUM = TELEGRAM_PHOTO_MAX_DIMENSIONS_SUM
    MAX_ASPECT_RATIO = TELEGRAM_PHOTO_MAX_ASPECT_RATIO
    TIMEOUT_SECONDS = 12.0

    def __init__(self, slots: asyncio.Semaphore) -> None:
        self._slots = slots

    async def prepare(self, media: PreparedMedia, *, force: bool = False) -> PreparedMedia:
        if media.kind != MediaKind.PHOTO or not isinstance(media.file, BufferedInputFile):
            return media

        async with self._slots:
            try:
                async with asyncio.timeout(self.TIMEOUT_SECONDS):
                    payload = await asyncio.to_thread(self._prepare_payload, media.file.data, force=force)
            except TimeoutError:
                await logger.adebug(
                    "[Medias] Photo compression timed out",
                    source_url=media.source_url,
                    timeout_seconds=self.TIMEOUT_SECONDS,
                )
                return media
            except Exception:  # ruff: ignore[blind-except]
                return media

        if not payload:
            return media
        filename = f"{Path(media.filename).stem or 'photo'}_compressed.jpg"
        return replace(media, file=BufferedInputFile(payload, filename), filename=filename)

    async def prepare_many(self, media_items: tuple[PreparedMedia, ...], *, force: bool) -> tuple[PreparedMedia, ...]:
        prepared = list(media_items)
        tasks: dict[int, asyncio.Task[PreparedMedia]] = {}
        async with asyncio.TaskGroup() as task_group:
            for index, media in enumerate(media_items):
                if media.kind != MediaKind.PHOTO or not isinstance(media.file, BufferedInputFile):
                    continue
                tasks[index] = task_group.create_task(self.prepare(media, force=force), name=f"media-photo:{index}")
        for index, task in tasks.items():
            prepared[index] = task.result()
        return tuple(prepared)

    @classmethod
    def _prepare_payload(cls, payload: bytes, *, force: bool) -> bytes | None:
        if not force and len(payload) <= cls.SAFE_LIMIT_BYTES:
            needs_resize = photo_payload_needs_resize(
                payload, max_dimensions_sum=cls.MAX_DIMENSIONS_SUM, max_aspect_ratio=cls.MAX_ASPECT_RATIO
            )
            if not needs_resize:
                return None
        return compress_photo_payload_to_safe_jpeg(
            payload,
            safe_limit_bytes=cls.SAFE_LIMIT_BYTES,
            max_dimensions_sum=cls.MAX_DIMENSIONS_SUM,
            max_aspect_ratio=cls.MAX_ASPECT_RATIO,
        )

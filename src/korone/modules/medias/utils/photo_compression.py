from __future__ import annotations

from io import BytesIO
from typing import Final

from PIL import Image, ImageOps

DEFAULT_QUALITY_STEPS: Final[tuple[int, ...]] = (88, 76, 64, 52, 40)
DEFAULT_MAX_PASSES: Final[int] = 6


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


def compress_photo_payload_to_safe_jpeg(
    payload: bytes,
    *,
    safe_limit_bytes: int,
    max_dimensions_sum: int,
    max_aspect_ratio: int,
    quality_steps: tuple[int, ...] = DEFAULT_QUALITY_STEPS,
    max_passes: int = DEFAULT_MAX_PASSES,
) -> bytes | None:
    best: bytes | None = None

    with Image.open(BytesIO(payload)) as source_image:
        base = ImageOps.exif_transpose(source_image)
        if base.mode not in {"RGB", "L"}:
            rgba = base.convert("RGBA")
            background = Image.new("RGBA", rgba.size, "white")
            background.alpha_composite(rgba)
            base = background.convert("RGB")
        elif base.mode == "L":
            base = base.convert("RGB")

        constrained_base = _constrain_photo_dimensions(
            base, max_dimensions_sum=max_dimensions_sum, max_aspect_ratio=max_aspect_ratio
        )
        try:
            base_width, base_height = constrained_base.size
            if base_width < 1 or base_height < 1:
                return None

            width, height = base_width, base_height
            for _ in range(max_passes):
                if width == base_width and height == base_height:
                    candidate_image = constrained_base
                else:
                    candidate_image = constrained_base.resize((width, height), Image.Resampling.LANCZOS)

                try:
                    encoded, smallest_for_pass, best = _encode_candidate_jpeg(
                        candidate_image, safe_limit_bytes=safe_limit_bytes, quality_steps=quality_steps, best=best
                    )
                finally:
                    if candidate_image is not constrained_base:
                        candidate_image.close()

                if encoded is not None:
                    return encoded
                if not smallest_for_pass:
                    break

                ratio = safe_limit_bytes / len(smallest_for_pass)
                if ratio >= 1:
                    break

                shrink = max(0.55, min(0.9, (ratio**0.5) * 0.97))
                next_width = max(1, int(width * shrink))
                next_height = max(1, int(height * shrink))
                if next_width == width and next_height == height:
                    next_width = max(1, int(width * 0.9))
                    next_height = max(1, int(height * 0.9))

                width, height = next_width, next_height
        finally:
            if constrained_base is not base:
                constrained_base.close()

    return best if best and len(best) <= safe_limit_bytes else None

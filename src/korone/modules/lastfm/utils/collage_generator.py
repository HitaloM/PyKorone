from __future__ import annotations

import io
from functools import partial
from typing import TYPE_CHECKING

from anyio import create_task_group
from anyio.to_thread import run_sync
from PIL import Image, ImageDraw, ImageFont

from korone.logging import get_logger

from .image_filter import get_biggest_lastfm_image

if TYPE_CHECKING:
    from io import BytesIO

    from .types import LastFMAlbum

logger = get_logger(__name__)

THUMB_SIZE = 300
FONT_SIZE = 24
LINE_SPACING = 2
TEXT_POSITION_OFFSET = 8
FONT_CANDIDATES: tuple[str, ...] = (
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
    "DejaVuSans.ttf",
)


async def fetch_album_art(album: LastFMAlbum) -> Image.Image:
    try:
        image_data = await get_biggest_lastfm_image(album)
        if image_data:
            return await run_sync(open_image, image_data)
    except Exception as exc:  # noqa: BLE001
        await logger.aexception("Failed to fetch album art: %s", exc)

    return await run_sync(create_placeholder)


async def fetch_album_arts(albums: list[LastFMAlbum]) -> list[Image.Image]:
    results: list[Image.Image | None] = [None] * len(albums)

    async def fetch(index: int, album: LastFMAlbum) -> None:
        results[index] = await fetch_album_art(album)

    async with create_task_group() as tg:
        for index, album in enumerate(albums):
            tg.start_soon(fetch, index, album)

    return [img for img in results if img is not None]


async def process_single_image(
    index: int, item: LastFMAlbum, img: Image.Image, results: list[Image.Image | None], *, show_text: bool = True
) -> None:
    try:
        results[index] = await run_sync(partial(prepare_single_image, show_text=show_text), item, img)
    except Exception as exc:  # noqa: BLE001
        await logger.aexception("Failed to process image at index %s: %s", index, exc)
        results[index] = None


async def create_album_collage(
    albums: list[LastFMAlbum], *, collage_size: tuple[int, int] = (3, 3), show_text: bool = True
) -> io.BytesIO:
    rows, cols = collage_size
    total_albums = min(len(albums), rows * cols)

    collage = Image.new("RGB", (THUMB_SIZE * cols, THUMB_SIZE * rows))

    album_images = await fetch_album_arts(albums[:total_albums])
    processed_results: list[Image.Image | None] = [None] * total_albums

    async with create_task_group() as tg:
        for index, (item, img) in enumerate(zip(albums[:total_albums], album_images, strict=False)):
            runner = partial(process_single_image, show_text=show_text)
            tg.start_soon(runner, index, item, img, processed_results)

    for index, processed_image in enumerate(processed_results):
        if processed_image is None:
            continue

        x, y = (index % cols) * THUMB_SIZE, (index // cols) * THUMB_SIZE
        await run_sync(paste_image, collage, processed_image, x, y)
        processed_image.close()

    collage_bytes = io.BytesIO()
    await run_sync(collage.save, collage_bytes, "PNG")
    collage_bytes.seek(0)

    return collage_bytes


def create_placeholder() -> Image.Image:
    image = Image.new("RGB", (THUMB_SIZE, THUMB_SIZE), color=(40, 40, 40))
    draw = ImageDraw.Draw(image)
    draw.rectangle(((0, 0), (THUMB_SIZE - 1, THUMB_SIZE - 1)), outline=(80, 80, 80))
    return image


def open_image(source: BytesIO) -> Image.Image:
    source.seek(0)
    image = Image.open(source)
    image.load()
    return image


def load_font(font_size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    for font_path in FONT_CANDIDATES:
        try:
            return ImageFont.truetype(font_path, font_size)
        except OSError:
            continue
    return ImageFont.load_default()


def wrap_text_to_width(
    draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont | ImageFont.ImageFont, max_width: int
) -> list[str]:
    words = text.split()
    if not words:
        return [""]

    lines: list[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if draw.textlength(candidate, font=font) <= max_width:
            current = candidate
        else:
            lines.append(current)
            current = word
    lines.append(current)
    return lines


def apply_bottom_gradient(img: Image.Image, start_y: int, *, max_alpha: int = 200, end_alpha: int = 255) -> None:
    if start_y >= img.height:
        return

    base = img.convert("RGBA")
    height = img.height - start_y
    if height <= 0:
        return

    overlay = Image.new("RGBA", (img.width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    for i in range(height):
        ratio = i / max(height - 1, 1)
        alpha = int(max_alpha + (end_alpha - max_alpha) * ratio)
        draw.line([(0, i), (img.width, i)], fill=(0, 0, 0, alpha))

    base_region = base.crop((0, start_y, img.width, img.height))
    blended_region = Image.alpha_composite(base_region, overlay)
    base.paste(blended_region, (0, start_y))
    img.paste(base.convert(img.mode))


def add_text_to_image(img: Image.Image, text: str, font_size: int) -> None:
    font = load_font(font_size)
    draw = ImageDraw.Draw(img)
    max_width = img.width - (TEXT_POSITION_OFFSET * 2)

    wrapped_lines: list[str] = []
    for raw_line in text.split("\n"):
        wrapped_lines.extend(wrap_text_to_width(draw, raw_line, font, max_width))

    text_block = "\n".join(wrapped_lines)
    bbox = draw.multiline_textbbox((0, 0), text_block, font=font, spacing=LINE_SPACING)
    text_height = bbox[3] - bbox[1]
    text_x = TEXT_POSITION_OFFSET
    text_y = img.height - text_height - TEXT_POSITION_OFFSET

    gradient_start = int(max(0, text_y - (TEXT_POSITION_OFFSET * 2)))
    apply_bottom_gradient(img, gradient_start)
    draw.multiline_text((text_x, text_y), text_block, font=font, fill="white", spacing=LINE_SPACING)


def prepare_single_image(item: LastFMAlbum, img: Image.Image, *, show_text: bool) -> Image.Image:
    resized = img.resize((THUMB_SIZE, THUMB_SIZE), Image.Resampling.LANCZOS).convert("RGB")
    if show_text:
        artist_name = item.artist.name if item.artist is not None else ""
        text = f"{artist_name}\n{item.name}\n{item.playcount} plays"
        add_text_to_image(resized, text, FONT_SIZE)
    img.close()
    return resized


def paste_image(collage: Image.Image, processed_image: Image.Image, x: int, y: int) -> None:
    collage.paste(processed_image, (x, y))

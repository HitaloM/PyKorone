from __future__ import annotations

import io
from functools import partial
from typing import TYPE_CHECKING

from anyio import create_task_group
from anyio.to_thread import run_sync
from PIL import Image, ImageDraw, ImageFont

from korone.logger import get_logger

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


async def fetch_album_art(album: LastFMAlbum) -> BytesIO | None:
    try:
        return await get_biggest_lastfm_image(album)
    except Exception as exc:  # noqa: BLE001
        await logger.aexception("Failed to fetch album art: %s", exc)
    return None


async def fetch_album_arts(albums: list[LastFMAlbum]) -> list[BytesIO | None]:
    results: list[BytesIO | None] = [None] * len(albums)

    async def fetch(index: int, album: LastFMAlbum) -> None:
        results[index] = await fetch_album_art(album)

    async with create_task_group() as tg:
        for index, album in enumerate(albums):
            tg.start_soon(fetch, index, album)

    return results


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
    total_albums = rows * cols
    albums_with_images = [album for album in albums if album.images]
    selected_albums = albums_with_images[:total_albums]

    collage = Image.new("RGBA", (THUMB_SIZE * cols, THUMB_SIZE * rows), (0, 0, 0, 255))

    tiles_bytes_vec = await fetch_album_arts(selected_albums)

    for index, album in enumerate(selected_albums):
        tile_bytes = tiles_bytes_vec[index]
        row = index // cols
        col = index % cols
        tile_x = col * THUMB_SIZE
        tile_y = row * THUMB_SIZE

        if tile_bytes is not None:
            tile = await run_sync(load_tile_image, tile_bytes)
            if tile is not None:
                collage.paste(tile, (tile_x, tile_y), tile)

        if show_text:
            artist_name = album.artist.name if album.artist is not None else ""
            text = f"{album.name}\n{artist_name}\n{album.playcount} plays"
            text_image = Image.new("RGBA", (THUMB_SIZE, THUMB_SIZE), (0, 0, 0, 0))
            add_text_to_image(text_image, text, FONT_SIZE)
            collage.paste(text_image, (tile_x, tile_y), text_image)

    collage_bytes = io.BytesIO()
    await run_sync(collage.convert("RGB").save, collage_bytes, "JPEG")
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
    lines = text.split("\n")
    base_y = img.height - 70
    line_step = 20
    text_x = 10

    for idx, line in enumerate(lines):
        text_y = base_y + (idx * line_step)
        draw_text_with_outline(draw, text_x, text_y, line, font)


def draw_text_with_outline(
    draw: ImageDraw.ImageDraw,
    x: int,
    y: int,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    *,
    outline_offset: int = 2,
    text_color: tuple[int, int, int, int] = (255, 255, 255, 255),
    outline_color: tuple[int, int, int, int] = (0, 0, 0, 255),
) -> None:
    offsets = (
        (-outline_offset, -outline_offset),
        (-outline_offset, 0),
        (-outline_offset, outline_offset),
        (0, -outline_offset),
        (0, outline_offset),
        (outline_offset, -outline_offset),
        (outline_offset, 0),
        (outline_offset, outline_offset),
    )
    for dx, dy in offsets:
        draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
    draw.text((x, y), text, font=font, fill=text_color)


def load_tile_image(source: BytesIO) -> Image.Image | None:
    try:
        tile = open_image(source).convert("RGBA")
    except Exception:  # noqa: BLE001
        return None
    if tile.width > THUMB_SIZE:
        tile.thumbnail((THUMB_SIZE, THUMB_SIZE), Image.Resampling.LANCZOS)
    return tile


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

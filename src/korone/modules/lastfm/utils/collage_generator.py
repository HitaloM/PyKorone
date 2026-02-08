from __future__ import annotations

import asyncio
import io
from functools import cache
from typing import TYPE_CHECKING

from PIL import Image, ImageDraw, ImageFont

from korone.logger import get_logger

from .image_filter import get_biggest_lastfm_image

if TYPE_CHECKING:
    from .types import LastFMAlbum

logger = get_logger(__name__)

THUMB_SIZE: int = 300
FONT_SIZE: int = 24
TEXT_PADDING: int = 10
FONT_CANDIDATES: str = "data/NotoSans-Regular.ttf"


@cache
def load_font(size: int = FONT_SIZE) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype(FONT_CANDIDATES, size)
    except OSError:
        pass
    return ImageFont.load_default()


async def fetch_album_art(album: LastFMAlbum) -> io.BytesIO | None:
    try:
        return await get_biggest_lastfm_image(album)
    except OSError as exc:
        await logger.aexception("Failed to fetch album art: %s", exc)
    return None


def wrap_text(text: str, font: ImageFont.FreeTypeFont | ImageFont.ImageFont, max_width: int) -> list[str]:
    lines = []
    for paragraph in text.split("\n"):
        if font.getlength(paragraph) <= max_width:
            lines.append(paragraph)
            continue

        words = paragraph.split()
        current_line = ""
        for word in words:
            test_line = f"{current_line} {word}".strip()
            if font.getlength(test_line) <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        if current_line:
            lines.append(current_line)
    return lines


def process_tile(data: io.BytesIO | None, album: LastFMAlbum, *, show_text: bool = True) -> Image.Image:
    tile: Image.Image
    if data:
        try:
            data.seek(0)
            with Image.open(data) as fetched_img:
                fetched_img.load()
                if fetched_img.width > THUMB_SIZE or fetched_img.height > THUMB_SIZE:
                    tile = fetched_img.resize((THUMB_SIZE, THUMB_SIZE), Image.Resampling.LANCZOS)
                else:
                    tile = fetched_img.copy()
                tile = tile.convert("RGBA")
        except OSError, ValueError:
            tile = _create_placeholder()
    else:
        tile = _create_placeholder()

    if show_text:
        draw = ImageDraw.Draw(tile)
        font = load_font()

        artist = album.artist.name if album.artist else "Unknown Artist"
        raw_text = f"{album.name}\n{artist}\n{album.playcount} plays"

        max_width = THUMB_SIZE - (TEXT_PADDING * 2)

        wrapped_lines = wrap_text(raw_text, font, max_width)

        current_y = THUMB_SIZE - TEXT_PADDING

        for line in reversed(wrapped_lines):
            bbox = font.getbbox(line)
            line_height = bbox[3] - bbox[1]

            current_y -= line_height + 4

            draw.text(
                (TEXT_PADDING, current_y),
                line,
                font=font,
                fill=(255, 255, 255, 255),
                stroke_width=2,
                stroke_fill=(0, 0, 0, 255),
            )

    return tile


def _create_placeholder() -> Image.Image:
    img = Image.new("RGBA", (THUMB_SIZE, THUMB_SIZE), (40, 40, 40, 255))
    draw = ImageDraw.Draw(img)
    draw.rectangle(((0, 0), (THUMB_SIZE - 1, THUMB_SIZE - 1)), outline=(80, 80, 80))
    return img


async def create_album_collage(
    albums: list[LastFMAlbum], *, collage_size: tuple[int, int] = (3, 3), show_text: bool = True
) -> io.BytesIO:
    rows, cols = collage_size
    limit = rows * cols
    target_albums = [a for a in albums if a.images][:limit]
    images_data: list[io.BytesIO | None] = [None] * len(target_albums)

    async def _fetch_and_store(index: int, album: LastFMAlbum) -> None:
        images_data[index] = await fetch_album_art(album)

    async with asyncio.TaskGroup() as tg:
        for idx, album_obj in enumerate(target_albums):
            tg.create_task(_fetch_and_store(idx, album_obj))

    def assemble_collage() -> io.BytesIO:
        collage = Image.new("RGBA", (cols * THUMB_SIZE, rows * THUMB_SIZE), (0, 0, 0, 255))

        for i, album_obj in enumerate(target_albums):
            tile = process_tile(images_data[i], album_obj, show_text=show_text)
            row, col = divmod(i, cols)
            collage.paste(tile, (col * THUMB_SIZE, row * THUMB_SIZE))
            tile.close()

        out = io.BytesIO()
        collage.convert("RGB").save(out, "JPEG", quality=90)
        out.seek(0)
        return out

    return await asyncio.to_thread(assemble_collage)

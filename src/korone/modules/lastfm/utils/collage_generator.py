# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import io
from datetime import timedelta

from anyio import create_task_group, to_thread
from PIL import Image, ImageDraw, ImageFont

from korone.utils.caching import cache
from korone.utils.logging import get_logger

from .image_filter import get_biggest_lastfm_image
from .types import LastFMAlbum

logger = get_logger(__name__)

THUMB_SIZE = 300
DEFAULT_IMAGE_PATH = "resources/lastfm/dummy_image.png"
FONT_PATH = "resources/lastfm/DejaVuSans-Bold.ttf"
FONT_SIZE = 24
TEXT_POSITION_OFFSET = 10


async def add_text_to_image(
    img: Image.Image, text: str, font_path: str = FONT_PATH, font_size: int = FONT_SIZE
) -> None:
    try:
        font = ImageFont.truetype(font_path, font_size)

        def blocking_add_text_to_image() -> None:
            draw = ImageDraw.Draw(img)
            lines = text.split("\n")
            text_height = len(lines) * font_size
            text_x, text_y = TEXT_POSITION_OFFSET, img.height - text_height - TEXT_POSITION_OFFSET

            # Create semi-transparent gradient for text background
            mask = Image.linear_gradient("L").resize((img.width, int(text_height) + 20))
            gradient = Image.new("RGB", (img.width, int(text_height) + 20), "black")
            gradient.putalpha(mask)
            img.paste(
                gradient, (0, int(img.height - text_height - 20), img.width, img.height), gradient
            )

            # Draw text with border for better visibility
            for line in lines:
                # Draw text outline
                for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                    draw.text((text_x + dx, text_y + dy), line, font=font, fill="black")
                # Draw main text
                draw.text((text_x, text_y), line, font=font, fill="white")
                text_y += font_size

        await to_thread.run_sync(blocking_add_text_to_image)

    except Exception as e:
        await logger.aexception("Failed to add text to image: %s", e)


async def fetch_album_art(album: LastFMAlbum) -> Image.Image:
    try:
        image_data = await get_biggest_lastfm_image(album)
        if image_data:
            return Image.open(image_data)
    except Exception as e:
        await logger.aexception("Failed to fetch album art: %s", e)

    return Image.open(DEFAULT_IMAGE_PATH)


async def fetch_album_arts(albums: list[LastFMAlbum]) -> list[Image.Image]:
    results: list[Image.Image | None] = [None] * len(albums)

    async def fetch(index: int, album: LastFMAlbum) -> None:
        results[index] = await fetch_album_art(album)

    async with create_task_group() as tg:
        for index, album in enumerate(albums):
            tg.start_soon(fetch, index, album)

    return [img for img in results if img is not None]


async def process_single_image(
    index: int,
    item: LastFMAlbum,
    img: Image.Image,
    collage: Image.Image,
    cols: int,
    show_text: bool = True,
) -> None:
    try:
        # Resize the image to thumbnail size
        img = img.resize((THUMB_SIZE, THUMB_SIZE), Image.Resampling.LANCZOS)

        # Add text if needed
        if show_text:
            artist_name = item.artist.name if item.artist is not None else ""
            text = f"{artist_name}\n{item.name}\n{item.playcount} plays"
            await add_text_to_image(img, text)

        # Calculate position in the collage
        x, y = (index % cols) * THUMB_SIZE, (index // cols) * THUMB_SIZE

        # Paste image into collage
        collage.paste(img, (x, y))

    except Exception as e:
        await logger.aexception("Failed to process image at index %s: %s", index, e)


@cache(ttl=timedelta(days=1))
async def create_album_collage(
    albums: list[LastFMAlbum], collage_size: tuple[int, int] = (3, 3), show_text: bool = True
) -> io.BytesIO:
    rows, cols = collage_size
    total_albums = min(len(albums), rows * cols)

    # Create blank collage image
    collage = Image.new("RGB", (THUMB_SIZE * cols, THUMB_SIZE * rows))

    album_images = await fetch_album_arts(albums[:total_albums])

    async with create_task_group() as tg:
        for index, (item, img) in enumerate(
            zip(albums[:total_albums], album_images, strict=False)
        ):
            tg.start_soon(process_single_image, index, item, img, collage, cols, show_text)

    collage_bytes = io.BytesIO()
    await to_thread.run_sync(collage.save, collage_bytes, "PNG")
    collage_bytes.seek(0)

    return collage_bytes

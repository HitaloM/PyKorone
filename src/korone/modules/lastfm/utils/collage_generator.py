# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import io
from datetime import timedelta
from io import BytesIO

from anyio import create_task_group
from PIL import Image, ImageDraw, ImageFont

from korone.utils.caching import cache
from korone.utils.concurrency import run_blocking
from korone.utils.logging import get_logger

from .image_filter import get_biggest_lastfm_image
from .types import LastFMAlbum

logger = get_logger(__name__)

THUMB_SIZE = 300
DEFAULT_IMAGE_PATH = "resources/lastfm/dummy_image.png"
FONT_PATH = "resources/lastfm/DejaVuSans-Bold.ttf"
FONT_SIZE = 24
TEXT_POSITION_OFFSET = 10


async def fetch_album_art(album: LastFMAlbum) -> Image.Image:
    try:
        image_data = await get_biggest_lastfm_image(album)
        if image_data:
            return await run_blocking(open_image, image_data)
    except Exception as e:
        await logger.aexception("Failed to fetch album art: %s", e)

    return await run_blocking(open_image, DEFAULT_IMAGE_PATH)


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
    results: list[Image.Image | None],
    show_text: bool = True,
) -> None:
    try:
        results[index] = await run_blocking(prepare_single_image, item, img, show_text)
    except Exception as e:
        await logger.aexception("Failed to process image at index %s: %s", index, e)
        results[index] = None


@cache(ttl=timedelta(days=1))
async def create_album_collage(
    albums: list[LastFMAlbum], collage_size: tuple[int, int] = (3, 3), show_text: bool = True
) -> io.BytesIO:
    rows, cols = collage_size
    total_albums = min(len(albums), rows * cols)

    collage = Image.new("RGB", (THUMB_SIZE * cols, THUMB_SIZE * rows))

    album_images = await fetch_album_arts(albums[:total_albums])
    processed_results: list[Image.Image | None] = [None] * total_albums

    async with create_task_group() as tg:
        for index, (item, img) in enumerate(
            zip(albums[:total_albums], album_images, strict=False)
        ):
            tg.start_soon(process_single_image, index, item, img, processed_results, show_text)

    for index, processed_image in enumerate(processed_results):
        if processed_image is None:
            continue

        x, y = (index % cols) * THUMB_SIZE, (index // cols) * THUMB_SIZE
        await run_blocking(paste_image, collage, processed_image, x, y)
        processed_image.close()

    collage_bytes = io.BytesIO()
    await run_blocking(collage.save, collage_bytes, "PNG")
    collage_bytes.seek(0)

    return collage_bytes


def open_image(source: str | BytesIO) -> Image.Image:
    if isinstance(source, BytesIO):
        source.seek(0)
    image = Image.open(source)
    image.load()
    return image


def add_text_to_image(img: Image.Image, text: str, font_path: str, font_size: int) -> None:
    font = ImageFont.truetype(font_path, font_size)
    draw = ImageDraw.Draw(img)
    lines = text.split("\n")
    text_height = len(lines) * font_size
    text_x, text_y = TEXT_POSITION_OFFSET, img.height - text_height - TEXT_POSITION_OFFSET

    mask = Image.linear_gradient("L").resize((img.width, int(text_height) + 20))
    gradient = Image.new("RGB", (img.width, int(text_height) + 20), "black")
    gradient.putalpha(mask)
    img.paste(gradient, (0, int(img.height - text_height - 20), img.width, img.height), gradient)

    for line in lines:
        for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            draw.text((text_x + dx, text_y + dy), line, font=font, fill="black")
        draw.text((text_x, text_y), line, font=font, fill="white")
        text_y += font_size


def prepare_single_image(
    item: LastFMAlbum, img: Image.Image, show_text: bool
) -> Image.Image | None:
    try:
        resized = img.resize((THUMB_SIZE, THUMB_SIZE), Image.Resampling.LANCZOS)
        if show_text:
            artist_name = item.artist.name if item.artist is not None else ""
            text = f"{artist_name}\n{item.name}\n{item.playcount} plays"
            add_text_to_image(resized, text, FONT_PATH, FONT_SIZE)
        return resized
    finally:
        img.close()


def paste_image(collage: Image.Image, processed_image: Image.Image, x: int, y: int) -> None:
    collage.paste(processed_image, (x, y))

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import io
import random
import string
from pathlib import Path

import httpx
from PIL import Image, ImageDraw, ImageFont

from korone import app_dir
from korone.modules.lastfm.utils.api import LastFMAlbum
from korone.modules.lastfm.utils.image_filter import get_biggest_lastfm_image
from korone.utils.logging import log


async def fetch_image(url):
    try:
        async with httpx.AsyncClient(http2=True, timeout=20) as client:
            response = await client.get(url)
            response.raise_for_status()  # Ensure the request was successful
            return Image.open(io.BytesIO(response.content))
    except Exception:
        log.exception("Failed to fetch LastFM image")
        return None


def generate_random_file_path() -> Path:
    output_path = Path(app_dir / "tmp" / "lastfm")
    output_path.mkdir(exist_ok=True, parents=True)

    random_suffix = "".join(random.choices(string.ascii_letters + string.digits, k=8))
    return output_path / f"collage-{random_suffix}.png"


def add_text_to_image(img, text, font):
    draw = ImageDraw.Draw(img)
    lines = text.split("\n")
    font_size = font.size
    text_x, text_y = 10, img.height - (len(lines) * font_size) - 10

    # Create gradient mask
    mask = Image.new("L", (img.width, len(lines) * font_size + 20))
    for y in range(mask.height):
        for x in range(mask.width):
            mask.putpixel((x, y), int(255 * (y / mask.height)))

    # Apply gradient
    gradient = Image.new("RGB", (img.width, len(lines) * font_size + 20), "black")
    gradient.putalpha(mask)
    img.paste(gradient, (0, img.height - len(lines) * font_size - 20), gradient)

    # Draw text with border
    for line in lines:
        for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
            draw.text((text_x + dx, text_y + dy), line, font=font, fill="black")
        draw.text((text_x, text_y), line, font=font, fill="white")
        text_y += font_size


async def fetch_album_arts(albums: list[LastFMAlbum]) -> list[Image.Image]:
    results = []
    for album in albums:
        image_url = get_biggest_lastfm_image(album)
        if image_url:
            img = await fetch_image(image_url)
            if img:
                results.append(img)
    return results


async def create_album_collage(
    albums: list[LastFMAlbum], collage_size: tuple[int, int] = (3, 3), show_text: bool = True
) -> str:
    rows, cols = collage_size
    thumb_size = 300
    collage = Image.new("RGB", (thumb_size * cols, thumb_size * rows))

    font = ImageFont.truetype("resources/fonts/DejaVuSans-Bold.ttf", 24) if show_text else None

    album_images = await fetch_album_arts(albums[: rows * cols])

    for index, (item, img) in enumerate(zip(albums[: rows * cols], album_images, strict=False)):
        img = img.resize((thumb_size, thumb_size), Image.Resampling.LANCZOS)
        if show_text:
            text = f"{item.artist}\n{item.name}\n{item.playcount} plays"
            add_text_to_image(img, text, font)

        x, y = (index % cols) * thumb_size, (index // cols) * thumb_size
        collage.paste(img, (x, y))

    collage_path = generate_random_file_path()
    collage.save(collage_path)
    return collage_path.as_posix()

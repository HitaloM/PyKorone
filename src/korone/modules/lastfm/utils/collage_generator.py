# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio
import io
from datetime import timedelta

from PIL import Image, ImageDraw, ImageFont

from korone.utils.caching import cache

from .image_filter import get_biggest_lastfm_image
from .types import LastFMAlbum


async def add_text_to_image(img: Image.Image, text: str, font: ImageFont.FreeTypeFont) -> None:
    def blocking_add_text_to_image():
        draw = ImageDraw.Draw(img)
        lines = text.split("\n")
        font_size = font.size
        text_x, text_y = 10, img.height - (len(lines) * font_size) - 10

        # Create gradient mask
        mask = Image.new("L", (img.width, int(len(lines) * font_size + 20)))
        for y in range(mask.height):
            for x in range(mask.width):
                mask.putpixel((x, y), int(255 * (y / mask.height)))

        # Apply gradient
        gradient = Image.new("RGB", (img.width, int(len(lines) * font_size + 20)), "black")
        gradient.putalpha(mask)
        img.paste(gradient, (0, img.height - int(len(lines) * font_size) - 20), gradient)

        # Draw text with border
        for line in lines:
            for dx, dy in [(-1, -1), (-1, 1), (1, -1), (1, 1)]:
                draw.text((text_x + dx, text_y + dy), line, font=font, fill="black")
            draw.text((text_x, text_y), line, font=font, fill="white")
            text_y += font_size

    await asyncio.to_thread(blocking_add_text_to_image)


async def fetch_album_arts(albums: list[LastFMAlbum]) -> list[Image.Image]:
    async def fetch_art(album):
        image_url = await get_biggest_lastfm_image(album)
        return (
            Image.open(image_url)
            if image_url
            else Image.open("https://telegra.ph/file/d0244cd9b8bc7d0dd370d.png")
        )

    return [
        img
        for img in await asyncio.gather(*(fetch_art(album) for album in albums))
        if img is not None
    ]


@cache(timedelta(days=1))
async def create_album_collage(
    albums: list[LastFMAlbum], collage_size: tuple[int, int] = (3, 3), show_text: bool = True
) -> io.BytesIO:
    rows, cols = collage_size
    thumb_size = 300
    collage = Image.new("RGB", (thumb_size * cols, thumb_size * rows))

    font = ImageFont.truetype("resources/fonts/DejaVuSans-Bold.ttf", 24) if show_text else None

    album_images = await fetch_album_arts(albums[: rows * cols])

    async def process_image(index: int, item: LastFMAlbum, img: Image.Image) -> None:
        img = img.resize((thumb_size, thumb_size), Image.Resampling.LANCZOS)
        if font and show_text:
            text = f"{item.artist.name}\n{item.name}\n{item.playcount} plays"  # type: ignore
            await add_text_to_image(img, text, font)

        x, y = (index % cols) * thumb_size, (index // cols) * thumb_size
        collage.paste(img, (x, y))

    await asyncio.gather(
        *(
            process_image(index, item, img)
            for index, (item, img) in enumerate(
                zip(albums[: rows * cols], album_images, strict=False)
            )
        )
    )

    collage_bytes = io.BytesIO()
    await asyncio.to_thread(collage.save, collage_bytes, format="PNG")
    collage_bytes.seek(0)

    return collage_bytes

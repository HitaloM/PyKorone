from __future__ import annotations

import asyncio
from io import BytesIO
from typing import TYPE_CHECKING

import aiohttp
from PIL import Image, ImageDraw, ImageFont, ImageOps

from korone.utils.aiohttp_session import HTTPClient

if TYPE_CHECKING:
    from collections.abc import Sequence

    from .types import LastFMTopAlbum

TILE_PX = 300
MIN_SIZE = 1
MAX_SIZE = 7
JPEG_QUALITY = 90
DOWNLOAD_TIMEOUT_SECONDS = 20
MAX_PARALLEL_DOWNLOADS = 12

FontType = ImageFont.FreeTypeFont | ImageFont.ImageFont


class LastFMCollageError(Exception):
    """Raised when collage generation fails."""


def _truncate(value: str, limit: int) -> str:
    if len(value) <= limit:
        return value
    return f"{value[: limit - 3]}..."


def _load_font() -> FontType:
    for font_name in ("DejaVuSans.ttf", "Arial.ttf"):
        try:
            return ImageFont.truetype(font_name, 22)
        except OSError:
            continue
    return ImageFont.load_default()


async def _download_cover(
    url: str, *, request_timeout: aiohttp.ClientTimeout, semaphore: asyncio.Semaphore
) -> bytes | None:
    session = await HTTPClient.get_session()
    async with semaphore:
        try:
            async with session.get(url, timeout=request_timeout) as response:
                if response.status != 200:
                    return None
                return await response.read()
        except TimeoutError, aiohttp.ClientError:
            return None


async def _download_covers(urls: Sequence[str]) -> list[bytes | None]:
    if not urls:
        return []

    request_timeout = aiohttp.ClientTimeout(total=DOWNLOAD_TIMEOUT_SECONDS)
    semaphore = asyncio.Semaphore(min(len(urls), MAX_PARALLEL_DOWNLOADS))
    payloads: list[bytes | None] = [None] * len(urls)

    async def _worker(index: int, url: str) -> None:
        payloads[index] = await _download_cover(url, request_timeout=request_timeout, semaphore=semaphore)

    async with asyncio.TaskGroup() as tg:
        for index, url in enumerate(urls):
            tg.create_task(_worker(index, url))

    return payloads


def _render_tile_overlay(image: Image.Image, album: LastFMTopAlbum, *, font: FontType) -> None:
    draw = ImageDraw.Draw(image)

    draw.text(
        (10, TILE_PX - 78),
        _truncate(album.name, 28),
        fill=(255, 255, 255),
        font=font,
        stroke_width=2,
        stroke_fill=(0, 0, 0),
    )
    draw.text(
        (10, TILE_PX - 53),
        _truncate(album.artist, 28),
        fill=(255, 255, 255),
        font=font,
        stroke_width=2,
        stroke_fill=(0, 0, 0),
    )
    draw.text(
        (10, TILE_PX - 28),
        f"{max(album.playcount, 0)} plays",
        fill=(255, 255, 255),
        font=font,
        stroke_width=2,
        stroke_fill=(0, 0, 0),
    )


def _build_tile(
    payload: bytes, album: LastFMTopAlbum, *, include_text: bool, font: FontType | None
) -> Image.Image | None:
    try:
        with Image.open(BytesIO(payload)) as source:
            converted = source.convert("RGB")
            try:
                tile = ImageOps.fit(converted, (TILE_PX, TILE_PX), method=Image.Resampling.LANCZOS)
            finally:
                converted.close()
    except OSError, ValueError:
        return None

    if include_text and font:
        _render_tile_overlay(tile, album, font=font)

    return tile


def _compose_collage_sync(
    *, albums: Sequence[LastFMTopAlbum], payloads: Sequence[bytes | None], size: int, include_text: bool
) -> bytes:
    image_size = TILE_PX * size
    collage = Image.new("RGB", (image_size, image_size), color=(0, 0, 0))
    font = _load_font() if include_text else None

    try:
        for index, (album, payload) in enumerate(zip(albums, payloads, strict=False)):
            if not payload:
                continue

            tile = _build_tile(payload, album, include_text=include_text, font=font)
            if tile is None:
                continue

            row = index // size
            col = index % size
            collage.paste(tile, (col * TILE_PX, row * TILE_PX))
            tile.close()

        output = BytesIO()
        collage.save(output, format="JPEG", quality=JPEG_QUALITY, optimize=True)
        return output.getvalue()
    finally:
        collage.close()


async def create_album_collage(*, albums: Sequence[LastFMTopAlbum], size: int, include_text: bool) -> bytes:
    valid_size = max(MIN_SIZE, min(MAX_SIZE, size))

    selectable = [album for album in albums if album.image_url][: valid_size * valid_size]
    if not selectable:
        msg = "No album covers found for this collage."
        raise LastFMCollageError(msg)

    payloads = await _download_covers([album.image_url for album in selectable if album.image_url])
    if not any(payloads):
        msg = "Could not download album covers for this collage."
        raise LastFMCollageError(msg)

    return await asyncio.to_thread(
        _compose_collage_sync, albums=selectable, payloads=payloads, size=valid_size, include_text=include_text
    )

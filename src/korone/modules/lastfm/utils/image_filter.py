from __future__ import annotations

import random
import string
from datetime import UTC, datetime, timedelta
from io import BytesIO
from typing import TYPE_CHECKING

import aiohttp

from korone.logger import get_logger

if TYPE_CHECKING:
    from .types import LastFMAlbum, LastFMTrack, LastFMUser

logger = get_logger(__name__)

DEFAULT_IMAGE_PLACEHOLDER = "2a96cbd8b46e442fc41c2b86b821562f"
SIZES_PRIORITY = {"small": 1, "medium": 2, "large": 3, "extralarge": 4}
HTTP_TIMEOUT = 20
CACHE_TTL = timedelta(hours=1)
_IMAGE_CACHE: dict[str, tuple[datetime, bytes, str]] = {}


def generate_random_filename(prefix: str = "LastFM", length: int = 8) -> str:
    random_suffix = "".join(random.choices(string.ascii_letters + string.digits, k=length))
    return f"{prefix}-{random_suffix}.jpeg"


def _get_cached(url: str) -> BytesIO | None:
    if url not in _IMAGE_CACHE:
        return None
    expires_at, data, filename = _IMAGE_CACHE[url]
    if datetime.now(tz=UTC) > expires_at:
        _IMAGE_CACHE.pop(url, None)
        return None
    file = BytesIO(data)
    file.name = filename
    return file


def _set_cached(url: str, data: bytes, filename: str) -> None:
    _IMAGE_CACHE[url] = (datetime.now(tz=UTC) + CACHE_TTL, data, filename)


async def get_biggest_lastfm_image(lfm_obj: LastFMAlbum | LastFMTrack | LastFMUser) -> BytesIO | None:
    if not lfm_obj.images:
        return None

    sorted_images = sorted(lfm_obj.images, key=lambda img: SIZES_PRIORITY.get(img.size, 0), reverse=True)

    for image in sorted_images:
        if not image.url or DEFAULT_IMAGE_PLACEHOLDER in image.url:
            continue

        if cached := _get_cached(image.url):
            return cached

        try:
            timeout = aiohttp.ClientTimeout(total=HTTP_TIMEOUT)
            async with aiohttp.ClientSession(timeout=timeout) as session, session.get(image.url) as response:
                response.raise_for_status()
                if response.status == 200:
                    content = await response.read()
                    filename = generate_random_filename()
                    _set_cached(image.url, content, filename)
                    file = BytesIO(content)
                    file.name = filename
                    return file

        except aiohttp.ClientResponseError as exc:
            await logger.aexception("[LastFM] HTTP error fetching image: %s", exc)
        except aiohttp.ClientError as exc:
            await logger.aexception("[LastFM] Request error fetching image: %s", exc)
        except Exception as exc:  # noqa: BLE001
            await logger.aexception("[LastFM] Unexpected error fetching image: %s", exc)

    return None

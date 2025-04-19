# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import random
import string
from datetime import timedelta
from io import BytesIO
from typing import Protocol

import httpx

from korone.utils.caching import cache
from korone.utils.logging import logger

from .types import LastFMAlbum, LastFMTrack, LastFMUser


class HasImages(Protocol):
    images: list | None


DEFAULT_IMAGE_PLACEHOLDER = "2a96cbd8b46e442fc41c2b86b821562f"
SIZES_PRIORITY = {"small": 1, "medium": 2, "large": 3, "extralarge": 4}
HTTP_TIMEOUT = 20


def generate_random_filename(prefix: str = "LastFM", length: int = 8) -> str:
    random_suffix = "".join(random.choices(string.ascii_letters + string.digits, k=length))
    return f"{prefix}-{random_suffix}.jpeg"


@cache(ttl=timedelta(hours=1))
async def get_biggest_lastfm_image(
    lfm_obj: LastFMAlbum | LastFMTrack | LastFMUser,
) -> BytesIO | None:
    if not lfm_obj.images:
        return None

    sorted_images = sorted(
        lfm_obj.images, key=lambda img: SIZES_PRIORITY.get(img.size, 0), reverse=True
    )

    for image in sorted_images:
        if not image.url or DEFAULT_IMAGE_PLACEHOLDER in image.url:
            continue

        try:
            async with httpx.AsyncClient(http2=True, timeout=HTTP_TIMEOUT) as client:
                response = await client.get(image.url)
                response.raise_for_status()

                if response.status_code == 200:
                    content = await response.aread()
                    file = BytesIO(content)
                    file.name = generate_random_filename()
                    return file

        except httpx.HTTPStatusError as e:
            await logger.aexception(f"[LastFM] Failed to fetch image: {e}")
        except httpx.RequestError as e:
            await logger.aexception(f"[LastFM] Request error while fetching image: {e}")
        except Exception as e:
            await logger.aexception(f"[LastFM] Unexpected error when fetching image: {e}")

    return None

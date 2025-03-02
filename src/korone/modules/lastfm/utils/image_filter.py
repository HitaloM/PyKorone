# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import random
import string
from datetime import timedelta
from io import BytesIO

import httpx

from korone.utils.caching import cache
from korone.utils.logging import logger

from .types import LastFMAlbum, LastFMTrack, LastFMUser


@cache(ttl=timedelta(hours=1))
async def get_biggest_lastfm_image(
    lfm_obj: LastFMAlbum | LastFMTrack | LastFMUser,
) -> BytesIO | None:
    if not lfm_obj.images:
        return None

    sizes_order = {"small": 1, "medium": 2, "large": 3, "extralarge": 4}

    sorted_images = sorted(
        lfm_obj.images, key=lambda img: sizes_order.get(img.size, 0), reverse=True
    )

    for image in sorted_images:
        if not image.url:
            continue

        try:
            if "2a96cbd8b46e442fc41c2b86b821562f" not in image.url:
                async with httpx.AsyncClient(http2=True, timeout=20) as client:
                    response = await client.get(image.url)
                    response.raise_for_status()
                    if response.status_code == 200:
                        content = await response.aread()

                        file = BytesIO(content)
                        random_suffix = "".join(
                            random.choices(string.ascii_letters + string.digits, k=8)
                        )
                        file.name = f"LastFM-{random_suffix}.jpeg"
                        return file
        except httpx.HTTPStatusError:
            await logger.aexception("[LastFM] Failed to fetch image.")
            continue

    return None

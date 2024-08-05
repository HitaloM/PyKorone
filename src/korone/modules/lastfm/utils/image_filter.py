# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from korone.modules.lastfm.utils.types import LastFMAlbum, LastFMTrack, LastFMUser


def get_biggest_lastfm_image(lfm_obj: LastFMAlbum | LastFMTrack | LastFMUser) -> str | None:
    if not lfm_obj.images:
        return None

    sizes_order = {"small": 1, "medium": 2, "large": 3, "extralarge": 4}

    sorted_images = sorted(
        lfm_obj.images, key=lambda img: sizes_order.get(img.size, 0), reverse=True
    )

    for image in sorted_images:
        if "2a96cbd8b46e442fc41c2b86b821562f" not in image.url:
            return image.url

    return None

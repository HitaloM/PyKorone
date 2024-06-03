# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from korone.modules.lastfm.utils.api import LastFMAlbum, LastFMTrack


def get_biggest_lastfm_image(lfm_obj: LastFMAlbum | LastFMTrack) -> str | None:
    placeholder = "https://telegra.ph/file/d0244cd9b8bc7d0dd370d.png"

    url = lfm_obj.images[-1].url if lfm_obj.images else placeholder
    if "2a96cbd8b46e442fc41c2b86b821562f" in url:
        return placeholder

    return url or None

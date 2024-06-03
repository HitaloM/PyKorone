# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from korone.modules.lastfm.utils.api import LastFMAlbum, LastFMTrack


def get_biggest_lastfm_image(lfm_obj: LastFMAlbum | LastFMTrack) -> str | None:
    placeholder = "https://telegra.ph/file/d0244cd9b8bc7d0dd370d.png"

    url = lfm_obj.images[-1].url if lfm_obj.images else placeholder
    if not url:
        return None

    return url

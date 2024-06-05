# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from korone.modules.lastfm.utils.api import LastFMAlbum, LastFMTrack, LastFMUser


def get_biggest_lastfm_image(lfm_obj: LastFMAlbum | LastFMTrack | LastFMUser) -> str | None:
    url = None
    if lfm_obj.images:
        url = lfm_obj.images[-1].url

    if url and "2a96cbd8b46e442fc41c2b86b821562f" in url:
        return None

    if url:
        return url

    return None

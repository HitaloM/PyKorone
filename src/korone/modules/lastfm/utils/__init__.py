# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from korone.modules.lastfm.utils.api import (
    LastFMClient,
    LastFMError,
    LastFMImage,
    LastFMTrack,
    TimePeriod,
)
from korone.modules.lastfm.utils.collage_generator import create_album_collage
from korone.modules.lastfm.utils.deezer_api import DeezerClient, DeezerError
from korone.modules.lastfm.utils.format_period import period_to_str
from korone.modules.lastfm.utils.format_tags import format_tags
from korone.modules.lastfm.utils.format_time import get_time_elapsed_str
from korone.modules.lastfm.utils.image_filter import get_biggest_lastfm_image
from korone.modules.lastfm.utils.parse_collage import EntryType, parse_collage_arg

__all__ = (
    "DeezerClient",
    "DeezerError",
    "EntryType",
    "LastFMClient",
    "LastFMError",
    "LastFMImage",
    "LastFMTrack",
    "TimePeriod",
    "create_album_collage",
    "format_tags",
    "get_biggest_lastfm_image",
    "get_time_elapsed_str",
    "parse_collage_arg",
    "period_to_str",
)
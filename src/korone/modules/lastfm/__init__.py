# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from babel.support import LazyProxy

from korone.utils.i18n import lazy_gettext as _


class ModuleInfo:
    name: LazyProxy = _("LastFM")
    summary: LazyProxy = _(
        "The LastFM module allows you to retrieve and display information about your favorite "
        "music artists, albums, and tracks. You can also view your recent plays and share them "
        "with your friends."
    )
    doc: LazyProxy = _(
        "<b>Commands:</b>\n"
        "- /setfm &lt;your username&gt;: Set your LastFM username.\n"
        "- /lfm: Get the track you are currently listening to or the last track you listened to.\n"
        "- /lfmr: Get your last 5 played tracks.\n"
        "- /lfmar: Get the artist you are currently listening to or the last artist you listened "
        "to.\n"
        "- /lfmal: Get the album you are currently listening to or the last album you listened "
        "to.\n"
        "- /lfmu: Get your total scrobbles, tracks, artists, and albums scrobbled.\n"
        "- /lfmc: Get a collage of your top albums."
        "\n\n<b>Examples:</b>\n"
        "- Generate a collage of your top 5x5 albums in a period of 7 days:\n"
        "-> <code>/lfmc 5 7d</code>\n\n"
        "- Generate a collage of your top 3x3 albums in a period of 1 month without text:\n"
        "-> <code>/lfmc 7 1m clean</code>\n\n"
        "<b>Notes:</b>\n"
        "Supported sizes: 1, 2, 3, 4, 5, 6, 7\n"
        "Supported Periods: 1d, 7d, 1m, 3m, 6m, 1y, all\n"
    )

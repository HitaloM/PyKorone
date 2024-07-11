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
        "- /setlfm &lt;your username&gt;: Set your LastFM username.\n"
        "- /lfm: Get the track you are currently listening to or the last track you listened to.\n"
        "- /lfmrecent: Get your last 5 played tracks.\n"
        "- /lfmartist: Get the artist you are currently listening to or the last artist you "
        "listened to.\n"
        "- /lfmalbum: Get the album you are currently listening to or the last album you listened "
        "to.\n"
        "- /lfmuser: Get your total scrobbles, tracks, artists, and albums scrobbled.\n"
        "- /lfmtop: Get your top artists, tracks, or albums.\n"
        "- /lfmcompat: Get the compatibility of your music taste with another user.\n"
        "- /lfmcollage: Get a collage of your top albums."
        "\n\n<b>Examples:</b>\n"
        "- Generate a collage of your top 5x5 albums in a period of 7 days:\n"
        "-> <code>/lfmcollage 5 7d</code>\n\n"
        "- Generate a collage of your top 7x7 albums in a period of 1 month without text:\n"
        "-> <code>/lfmcollage 7 1m clean</code>\n\n"
        "- Get your top 5 artists in a period of 1 year:\n"
        "-> <code>/lfmtop 1y</code>\n\n"
        "- Get your top 5 tracks of all time:\n"
        "-> <code>/lfmtop track</code>\n\n"
        "<b>Notes:</b>\n"
        "Supported sizes: 1, 2, 3, 4, 5, 6, 7\n"
        "Supported periods: 1d, 7d, 1m, 3m, 6m, 1y, all\n"
        "Supported types: artist, track, album"
    )

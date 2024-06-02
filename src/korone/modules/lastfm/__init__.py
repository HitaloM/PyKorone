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
        "- /now: Get the track you are currently listening to or the last track you listened to.\n"
        "- /recent: Get your last 5 played tracks."
    )

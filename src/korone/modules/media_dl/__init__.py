# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from babel.support import LazyProxy

from korone.utils.i18n import lazy_gettext as _


class ModuleInfo:
    name: LazyProxy = _("Media Downloader")
    summary: LazyProxy = _(
        "Some sites, when shared on Telegram by link, do not provide a preview of the image or "
        "video. That's where this module comes in. PyKorone will automatically detect the links "
        "of supported sites and upload the videos and images that are present in it!"
    )
    doc: LazyProxy = _("Actually, there is no documentation for this module. It just works!")

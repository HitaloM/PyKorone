# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from babel.support import LazyProxy

from korone.utils.i18n import lazy_gettext as _


class ModuleInfo:
    name: LazyProxy = _("Stickers")
    summary: LazyProxy = _(
        "This module contains commands for handling stickers and sticker packs."
    )
    doc: LazyProxy = _(
        "<b>Commands:</b>\n"
        "- /getsticker: Reply to a sticker to get it as a file and its file ID.\n"
        "- /kang: Reply to a sticker, image or video to add it to a sticker pack."
    )

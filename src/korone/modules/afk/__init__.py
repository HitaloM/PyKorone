# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from babel.support import LazyProxy

from korone.utils.i18n import lazy_gettext as _


class ModuleInfo:
    name: LazyProxy = _("AFK")
    summary: LazyProxy = _("AFK module allows you to set your status as AFK.")
    doc: LazyProxy = _("<b>Commands:</b>\n - /afk &lt;reason&gt;: Set your status as AFK.")

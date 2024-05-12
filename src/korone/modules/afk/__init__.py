# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from babel.support import LazyProxy

from korone.utils.i18n import lazy_gettext as _


class ModuleInfo:
    name: LazyProxy = _("AFK")
    summary: LazyProxy = _(
        "It can be challenging to communicate your availability status to others. This can lead "
        "to misunderstandings or missed messages when you're not available to respond.\n\n"
        "The AFK module addresses this issue by allowing you to set your status as "
        "'Away From Keyboard' (AFK). PyKorone will automatically respond to messages you receive "
        "while you're AFK, letting others know that you're currently unavailable."
    )
    doc: LazyProxy = _("<b>Commands:</b>\n - /afk &lt;reason&gt;: Set your status as AFK.")

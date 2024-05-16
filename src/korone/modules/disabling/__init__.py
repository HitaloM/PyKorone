# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from babel.support import LazyProxy

from korone.utils.i18n import lazy_gettext as _


class ModuleInfo:
    name: LazyProxy = _("Disabling")
    summary: LazyProxy = _(
        "Not everyone wants every feature Korone offers. Some commands are best left "
        "unused to prevent spam and abuse.\n\nThis allows you to disable some commonly used "
        "commands so that no one can use them. It also allows you to auto-delete "
        " to prevent people from bluetexting."
    )
    doc: LazyProxy = _(
        "<b>Admin Commands:</b>\n"
        '- /disable &lt;commandname&gt;: Stop users from using "commandname" in this group.'
        '- /enable &lt;commandname&gt;: Allow users from using "commandname" in this group.'
    )

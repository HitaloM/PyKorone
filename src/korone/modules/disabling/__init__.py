# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from babel.support import LazyProxy

from korone.utils.i18n import lazy_gettext as _


class ModuleInfo:
    name: LazyProxy = _("Disabling")
    summary: LazyProxy = _(
        "Not everyone wants every feature that PyKorone offers. "
        "Some commands are best left unused to avoid spam and abuse."
        "\n\nYou can disable commonly used commands to prevent their use "
        "and even autodelete them to stop people from bluetexting."
    )
    doc: LazyProxy = _(
        "<b>Commands:</b>\n"
        "- /disable <command> - Disable a command.\n"
        "- /enable <command> - Enable a command.\n"
    )

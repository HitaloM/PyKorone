# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from babel.support import LazyProxy

from korone.utils.i18n import lazy_gettext as _


class ModuleInfo:
    name: LazyProxy = _("Private Menu")
    summary: LazyProxy = _(
        "PyKorone uses intuitive menus to facilitate navigation. Some commands "
        "can be used in groups, but they will not return navigation buttons."
    )
    doc: LazyProxy = _(
        "<b>Commands:</b>\n"
        "- /start: Start the bot and show the main menu.\n"
        "- /help: Returns a list of available modules to get help.\n"
        "- /about: A brief description of the bot."
    )

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from babel.support import LazyProxy
from hairydogm.i18n import lazy_gettext as _


class ModuleInfo:
    """
    Class that represents information about the PM Menu module.

    This module is used to add commands and menus to the bot's PM.
    """

    name: LazyProxy = _("PM Menu")
    """The name of the module.
    The name of the module to be used in the bot's help command.

    :type: babel.support.LazyProxy
    """
    summary: LazyProxy = _("A module that adds a PM menu to the bot.")
    """A short summary of the module.
    Just a short sentence that explains what the module does.

    :type: babel.support.LazyProxy
    """
    doc: LazyProxy = _("A module that adds a PM menu to the bot.")
    """A short documentation of the module
    should explain what the module does and how to use it.

    :type: babel.support.LazyProxy
    """

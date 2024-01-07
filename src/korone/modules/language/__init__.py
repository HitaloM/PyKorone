# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from babel.support import LazyProxy

from korone.utils.i18n import lazy_gettext as _


class ModuleInfo:
    """
    Language module.

    This module is used to change the bot's language.

    Attributes
    ----------
    name : babel.support.LazyProxy
        The name of the module.
    summary : babel.support.LazyProxy
        A brief summary of the module's purpose.
    doc : babel.support.LazyProxy
        Detailed documentation of the module's commands.
    """

    name: LazyProxy = _("Languages")
    summary: LazyProxy = _(
        "Not all groups are fluent in English; some prefer "
        "PyKorone to respond in their native language.\n\n"
        "Translations can be used to change the language "
        "of the bot's replies to the language of your choice!"
    )
    doc: LazyProxy = _(
        "<b>Commands:</b>\n"
        "- /languages: Returns a menu with the languages available "
        "to be applied to the current chat."
        "\n- /language: Returns the language set for the current chat "
        "and its statistics."
        "\n\n<b>Note:</b>"
        "\nIn groups, the bot's language is set by the group's administrators."
    )

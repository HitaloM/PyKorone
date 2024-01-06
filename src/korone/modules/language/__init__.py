# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from babel.support import LazyProxy

from korone.database.impl import SQLite3Connection
from korone.utils.i18n import lazy_gettext as _

from .manager import create_tables


class ModuleInfo:
    """
    Information about the Language module.

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

    name: LazyProxy = _("Language")
    summary: LazyProxy = _("This module is used to change the bot's language.")
    doc: LazyProxy = _(
        """<b>Commands:</b>
- /languages: Returns a menu to change the bot's language.
- /language: Get current language and it's statistics.
"""
    )


async def __pre_setup__() -> None:  # noqa: N807
    """
    Perform pre-setup tasks.

    This function performs pre-setup tasks, including creating
    necessary tables in the SQLite3 database.
    """
    async with SQLite3Connection() as conn:
        await create_tables(conn)

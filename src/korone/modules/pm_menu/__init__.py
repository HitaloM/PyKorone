# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from dataclasses import dataclass


@dataclass
class ModuleInfo:
    """
    Class that represents information about the PM Menu module.

    This module is used to add commands and menus to the bot's PM.
    """

    name: str = "PM Menu"
    """The name of the module.
    The name of the module to be used in the bot's help command.

    :type: str
    """
    summary: str = "A module that adds a PM menu to the bot."
    """A short summary of the module.
    Just a short sentence that explains what the module does.

    :type: str
    """
    doc: str = "A module that adds a PM menu to the bot."
    """A short documentation of the module
    should explain what the module does and how to use it.

    :type: str
    """

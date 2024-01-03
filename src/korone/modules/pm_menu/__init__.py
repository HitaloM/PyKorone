# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from dataclasses import dataclass


@dataclass
class ModuleInfo:
    name: str = "PM Menu"
    summary: str = "A module that adds a PM menu to the bot."
    doc: str = "A module that adds a PM menu to the bot."

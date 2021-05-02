# This file is part of Korone (Telegram Bot)
# Copyright (C) 2021 AmanoTeam

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import re
from typing import Callable

from pyrogram import filters

from korone.config import prefix
from korone.handlers import COMMANDS_HELP


def load(client):
    def command_filter(
        command: str, group: str = "general", action: str = None, *args, **kwargs
    ) -> Callable:
        if command not in COMMANDS_HELP[group]["commands"].keys():
            COMMANDS_HELP[group]["commands"][command] = {"action": action or ""}
        prefixes = "".join(prefix)
        _prefix = f"^[{re.escape(prefixes)}]"
        return filters.regex(_prefix + command, *args, **kwargs)

    def int_filter(
        filter: str, group: str = "others", action: str = None, *args, **kwargs
    ) -> Callable:
        COMMANDS_HELP[group]["filters"][filter] = {"action": action or " "}
        return filters.regex(r"(?i)^{0}(\.|\?|\!)?$".format(filter), *args, **kwargs)

    filters.cmd = command_filter
    filters.int = int_filter

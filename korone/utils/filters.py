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

from pyrogram import Client, filters
from pyrogram.types import Message

from korone.config import PREFIXES
from korone.handlers import COMMANDS_HELP


def load(client):
    def command_filter(
        command: str,
        group: str = "general",
        action: str = None,
        flags: int = 0,
        *args,
        **kwargs,
    ) -> Callable:
        if command not in COMMANDS_HELP[group]["commands"].keys():
            COMMANDS_HELP[group]["commands"][command] = {"action": action or ""}
        pattern = r"^" + f"[{re.escape(''.join(PREFIXES))}]" + command

        async def func(flt, client: Client, message: Message):
            value = message.text or message.caption

            if bool(value):
                command = value.split()[0]
                if "@" in command:
                    b = command.split("@")[1]
                    if b.lower() == client.me.username.lower():
                        value = (
                            command.split("@")[0]
                            + (" " if len(value.split()) > 1 else "")
                            + " ".join(value.split()[1:])
                        )
                    else:
                        return False

                message.matches = list(flt.p.finditer(value)) or None

            return bool(message.matches)

        return filters.create(
            func, "RegexFilter", p=re.compile(pattern, flags, *args, **kwargs)
        )

    def int_filter(
        filter: str, group: str = "others", action: str = None, *args, **kwargs
    ) -> Callable:
        COMMANDS_HELP[group]["filters"][filter] = {"action": action or " "}
        return filters.regex(r"(?i)^{0}(\.|\?|\!)?$".format(filter), *args, **kwargs)

    filters.cmd = command_filter
    filters.int = int_filter

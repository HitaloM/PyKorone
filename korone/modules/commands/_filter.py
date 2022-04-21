# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2022 Amano Team
#
# This file is part of Korone (Telegram Bot)


import re
from typing import Callable, Dict, Optional

from pyrogram import Client, filters
from pyrogram.types import Message

from korone.config import PREFIXES
from korone.modules import COMMANDS_HELP


def command_filter(
    command: str,
    group: Optional[str] = "general",
    action: Optional[str] = None,
    flags: Optional[int] = 0,
    *args,
    **kwargs,
) -> Callable:
    if command not in COMMANDS_HELP[group]["commands"].keys():
        COMMANDS_HELP[group]["commands"][command]: Dict = {"action": action}

    pattern = r"^" + f"[{re.escape(''.join(PREFIXES))}]" + command
    if not pattern.endswith(("$", " ")):
        pattern += r"(?:\s|$)"

    async def func(flt, client: Client, message: Message, command=command):
        value = message.text
        if not value:
            return None

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

            message.matches = list(flt.p.finditer(value)) or None

        return bool(message.matches)

    return filters.create(
        func,
        "CommandsFilter",
        p=re.compile(pattern, flags, *args, **kwargs),
    )


filters.cmd = command_filter

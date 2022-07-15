# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2022 Amano Team

import re
from typing import Callable, Union

from pyrogram import Client, filters
from pyrogram.types import CallbackQuery, Message

from korone.config import PREFIXES
from korone.handlers import COMMANDS_HELP


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
    if not pattern.endswith(("$", " ")):
        pattern += r"(?:\s|$)"

    async def func(flt, client: Client, message: Message):
        value = message.text or message.caption

        if message.sender_chat:
            return

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
        "CommandHandler",
        p=re.compile(pattern, flags, *args, **kwargs),
    )


def int_filter(
    filter: str,
    group: str = "others",
    action: str = None,
    flags: int = 0,
    *args,
    **kwargs,
) -> Callable:
    COMMANDS_HELP[group]["filters"][filter] = {"action": action or " "}
    filter = r"(?i)^{0}(\.|\?|\!)?$".format(filter)

    async def func(flt, _, message: Message):
        value = message.text or message.caption

        if message.sender_chat:
            return

        if bool(value):
            message.matches = list(flt.p.finditer(value)) or None

        return bool(message.matches)

    return filters.create(
        func, "IntHandler", p=re.compile(filter, flags, *args, **kwargs)
    )


async def sudo_filter(_, client, union: Union[CallbackQuery, Message]) -> Callable:
    user = union.from_user
    if not user:
        return False
    return client.is_sudoer(user)


filters.cmd = command_filter
filters.int = int_filter
filters.sudoer = filters.create(sudo_filter, "FilterSudo")

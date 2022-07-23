# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo

from typing import Callable, List, Union

from pyrogram import filters
from pyrogram.types import CallbackQuery, Message


def command_filter(command: str, prefixes: List[str] = ["/", "!"]) -> Callable:
    return filters.command(command, prefixes)


async def sudo_filter(_, bot, union: Union[CallbackQuery, Message]) -> bool:
    user = union.from_user
    if not user:
        return False
    return bot.is_sudo(user)


filters.cmd = command_filter
filters.sudo = sudo_filter

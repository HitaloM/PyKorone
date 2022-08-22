# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

from typing import List

from pyrogram import filters
from pyrogram.types import Message

from ...bot import Korone
from ...database.disable import is_cmd_disabled
from ...utils.logger import log

DISABLABLE_CMDS: List[str] = []


def disableable_dec(command):
    log.debug(
        "[%s] Adding %s to the disableable commands...",
        Korone.__name__,
        command,
    )

    if command not in DISABLABLE_CMDS:
        DISABLABLE_CMDS.append(command)

    def decorator(func):
        async def wrapper(bot: Korone, message: Message, *args, **kwargs):
            chat_id = message.chat.id

            check = await is_cmd_disabled(chat_id, command)
            if check and not await filters.admin(bot, message):
                return

            return await func(bot, message, *args, **kwargs)

        return wrapper

    return decorator

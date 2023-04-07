# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo M. <https://github.com/HitaloM>

from typing import List, Union

from pyrogram import filters
from pyrogram.types import CallbackQuery, Message

from ..bot import Korone
from ..database.disable import is_cmd_disabled
from .logger import log

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
        async def wrapper(
            bot: Korone, union: Union[Message, CallbackQuery], *args, **kwargs
        ):
            message = union.message if isinstance(union, CallbackQuery) else union

            chat_id = message.chat.id

            check = await is_cmd_disabled(chat_id, command)
            if check and not await filters.admin(bot, message):
                return

            return await func(bot, message, *args, **kwargs)

        return wrapper

    return decorator

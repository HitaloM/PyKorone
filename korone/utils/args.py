# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2022 Amano Team
#
# This file is part of Korone (Telegram Bot)

from typing import Callable

from pyrogram.client import Client
from pyrogram.types import Message


def get_args(message: Message):
    args = message.text.split(" ")
    if len(args) == 1:
        return None
    return args[1:]


def get_args_str(message: Message):
    args = get_args(message)
    if args is None:
        return None
    return str(" ".join(args))


def get_cmd(message: Message):
    args = message.text.split()
    if args is None:
        return None
    return str(args.lower()[:1].split("@")[0])


def need_args_dec(num: int = 1):
    def wrapped(func: Callable) -> Callable:
        async def wrapped_func(client: Client, message: Message):
            args = get_args(message)
            if args is None:
                await message.reply_text("Give me args!")
                return
            return await func(client, message)

        return wrapped_func

    return wrapped

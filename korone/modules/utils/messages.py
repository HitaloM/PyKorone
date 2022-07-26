# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

from typing import Callable, Optional, Tuple

from pyrogram.types import Message


def is_command(message: Message) -> bool:
    text = message.text or message.caption
    return bool(text and text.startswith("/"))


def get_full_command(message: Message) -> Optional[Tuple[str, str]]:
    if is_command(message):
        text = message.text or message.caption
        command, *args = text.split(maxsplit=1)
        args = args[0] if args else ""
        return command, args


def get_command(message: Message, pure: bool = False) -> Optional[str]:
    command = get_full_command(message)
    if command:
        command = command[0]
        if pure:
            command, _, _ = command[1:].partition("@")
        return command


def get_args_str(message: Message) -> Optional[str]:
    command = get_full_command(message)
    if command:
        return command[1]


def get_args(message: Message) -> Optional[str]:
    command = get_full_command(message)
    if command:
        return command[1].split(" ")[0]


def need_args_dec(num: int = 1):
    def decorator(func) -> Callable:
        async def wrapper(*args, **kwargs):
            message = args[0]
            if len(message.text.split(" ")) > num:
                return await func(*args, **kwargs)
            await message.reply("I need arguments to perform this action.")

        return wrapper

    return decorator

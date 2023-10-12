# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo M. <https://github.com/HitaloM>

from collections.abc import Callable

from pyrogram.types import Message


def is_command(message: Message) -> bool:
    text = message.text or message.caption
    return bool(text and text.startswith("/"))


def get_full_command(message: Message) -> tuple[str, str] | None:
    if is_command(message):
        text = message.text or message.caption
        command, *args = text.split(maxsplit=1)
        args = args[0] if args else ""
        return command, args
    return None


def get_command(message: Message, pure: bool = False) -> str | None:
    command = get_full_command(message)
    if command:
        command = command[0]
        if pure:
            command, _, _ = command[1:].partition("@")
        return command
    return None


def get_args(message: Message) -> str | None:
    command = get_full_command(message)
    if command:
        return command[1]
    return None


def need_args_dec(num: int = 1):
    def decorator(func) -> Callable:
        async def wrapper(*args, **kwargs):
            message = args[1]
            if len(message.text.split(" ")) > num:
                return await func(*args, **kwargs)
            await message.reply("I need arguments to perform this action.")
            return None

        return wrapper

    return decorator

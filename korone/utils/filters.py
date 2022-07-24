# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

from typing import Callable, List, Union

from pyrogram import filters
from pyrogram.enums import ChatMemberStatus, ChatType
from pyrogram.types import CallbackQuery, Message


def command_filter(command: str, prefixes: List[str] = ["/", "!"]) -> Callable:
    return filters.command(command, prefixes)


async def sudo_filter(_, bot, union: Union[CallbackQuery, Message]) -> bool:
    user = union.from_user
    if not user:
        return False
    return bot.is_sudo(user)


async def filter_administrator(_, bot, union: Union[CallbackQuery, Message]) -> bool:
    is_callback = isinstance(union, CallbackQuery)
    message = union.message if is_callback else union
    chat = message.chat
    user = union.from_user

    if chat.type == ChatType.PRIVATE:
        return True

    member = await bot.get_chat_member(chat.id, user.id)
    return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)


filters.cmd = command_filter
filters.sudo = sudo_filter
filters.admin = filters.create(filter_administrator, "FilterAdministrator")

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

from email.message import Message

from pyrogram import filters
from pyrogram.enums import ChatType

from ..bot import Korone
from ..database.disable import (
    disable_command,
    enable_command,
    get_disabled_cmds,
    is_cmd_disabled,
)
from ..utils.disable import DISABLABLE_CMDS
from ..utils.languages import get_strings_dec
from ..utils.messages import get_args, need_args_dec


@Korone.on_message(filters.cmd("disableable"))
@get_strings_dec("disable")
async def list_disablable(bot: Korone, message: Message, strings):
    text = strings["disablable"]
    for command in sorted(DISABLABLE_CMDS):
        text += f"* <code>/{command}</code>\n"
    await message.reply(text)


@Korone.on_message(filters.cmd("disabled"))
@get_strings_dec("disable")
async def list_disabled(bot: Korone, message: Message, strings):
    if message.chat.type == ChatType.PRIVATE:
        await message.reply_text(strings["only_for_groups"])
        return

    disableds_cmds = await get_disabled_cmds(message.chat.id)
    if not disableds_cmds:
        await message.reply(
            strings["no_disabled_cmds"].format(chat_name=message.chat.title)
        )
        return

    text = strings["disabled_list"].format(chat_name=message.chat.title)
    for command in disableds_cmds:
        text += f"* <code>/{command[1]}</code>\n"
    await message.reply(text)


@Korone.on_message(filters.cmd("disable"))
@need_args_dec()
@get_strings_dec("disable")
async def disabler(bot: Korone, message: Message, strings):
    if message.chat.type == ChatType.PRIVATE:
        await message.reply_text(strings["only_for_groups"])
        return

    if not await filters.admin(bot, message):
        await message.reply_text(
            strings["only_for_admins"].format(chat_name=message.chat.title)
        )
        return

    command = get_args(message).lower()
    if command[0] in ("/", "!"):
        command = command[1:]

    if command not in DISABLABLE_CMDS:
        await message.reply(strings["wot_to_disable"])
        return

    if await is_cmd_disabled(message.chat.id, command):
        await message.reply(strings["already_disabled"])
        return

    await disable_command(message.chat.id, command)

    await message.reply(
        strings["disabled"].format(command=command, chat_name=message.chat.title)
    )


@Korone.on_message(filters.cmd("enable"))
@need_args_dec()
@get_strings_dec("disable")
async def enabler(bot: Korone, message: Message, strings):
    if message.chat.type == ChatType.PRIVATE:
        await message.reply_text(strings["only_for_groups"])
        return

    if not await filters.admin(bot, message):
        await message.reply_text(
            strings["only_for_admins"].format(chat_name=message.chat.title)
        )
        return

    command = get_args(message).lower()
    if command[0] in ("/", "!"):
        command = command[1:]

    if command not in DISABLABLE_CMDS:
        await message.reply(strings["wot_to_enable"])
        return

    if not await is_cmd_disabled(message.chat.id, command):
        await message.reply(strings["already_enabled"])
        return

    await enable_command(message.chat.id, command)

    await message.reply(
        strings["enabled"].format(command=command, chat_name=message.chat.title)
    )

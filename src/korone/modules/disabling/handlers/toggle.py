# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, CommandObject, IsAdmin, IsGroupChat
from korone.modules import COMMANDS, fetch_command_state
from korone.modules.disabling.database import set_command_state
from korone.utils.i18n import gettext as _


@router.message(Command("enable", disableable=False) & IsGroupChat & IsAdmin)
async def enable_command(client: Client, message: Message) -> None:
    await change_command_state(client, message, enable=True)


@router.message(Command("disable", disableable=False) & IsGroupChat & IsAdmin)
async def disable_command(client: Client, message: Message) -> None:
    await change_command_state(client, message, enable=False)


async def change_command_state(client: Client, message: Message, enable: bool) -> None:
    command_object = CommandObject(message).parse()
    command_args = command_object.args

    action = _("enable") if enable else _("disable")
    action_past = _("enabled") if enable else _("disabled")

    if not command_args:
        await message.reply(
            _(
                "You need to specify a command to {action}. "
                "Use <code>/{action} &lt;commandname&gt;</code>."
            ).format(action=action)
        )
        return

    command_args_list = command_args.split(" ")
    if len(command_args_list) > 1:
        await message.reply(
            _("You can only {action} one command at a time.").format(action=action)
        )
        return

    command_name = command_args_list[0]
    if command_name not in COMMANDS:
        await message.reply(
            _(
                "Unknown command to {action}:\n"
                "- <code>{command}</code>\n"
                "Check the /disableable!"
            ).format(action=action, command=command_name)
        )
        return

    command_state = await fetch_command_state(command_name)
    if command_state and bool(command_state[0]["state"]) == enable:
        await message.reply(_("This command is already {action}.").format(action=action_past))
        return

    await set_command_state(message.chat.id, command_name, state=enable)
    await message.reply(_("Command {action}.").format(action=action_past))

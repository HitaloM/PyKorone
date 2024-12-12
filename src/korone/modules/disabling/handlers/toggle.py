# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, CommandObject, IsGroupChat, UserIsAdmin
from korone.modules.core import COMMANDS, fetch_command_state
from korone.modules.disabling.database import set_command_state
from korone.utils.i18n import gettext as _


@router.message(Command("enable", disableable=False) & IsGroupChat & UserIsAdmin)
async def enable_command(client: Client, message: Message) -> None:
    await change_command_state(client, message, enable=True)


@router.message(Command("disable", disableable=False) & IsGroupChat & UserIsAdmin)
async def disable_command(client: Client, message: Message) -> None:
    await change_command_state(client, message, enable=False)


async def change_command_state(client: Client, message: Message, enable: bool) -> None:
    command_object = CommandObject(message).parse()
    command_name = command_object.args.split(" ")[0] if command_object.args else None

    if not command_name:
        await message.reply(
            _(
                "You need to specify a command to {action}. Use <code>/{action} "
                "&lt;commandname&gt;</code>."
            ).format(action=_("enable") if enable else _("disable"))
        )
        return

    if command_name not in COMMANDS:
        await message.reply(
            _(
                "Unknown command to {action}:\n- <code>{command}</code>\nCheck the /disableable!"
            ).format(action=_("enable") if enable else _("disable"), command=command_name)
        )
        return

    command_state = await fetch_command_state(command_name) or []
    command_state = [cs for cs in command_state if cs["chat_id"] == message.chat.id]

    if command_state and bool(command_state[0]["state"]) == enable:
        await message.reply(
            _("This command is already {action}.").format(
                action=_("enabled") if enable else _("disabled")
            )
        )
        return

    await set_command_state(message.chat.id, command_name, state=enable)
    await message.reply(
        _("Command {action}.").format(action=_("enabled") if enable else _("disabled"))
    )

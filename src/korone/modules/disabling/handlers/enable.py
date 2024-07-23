# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, CommandObject, IsAdmin, IsGroupChat
from korone.handlers.abstract import MessageHandler
from korone.modules import COMMANDS, fetch_command_state
from korone.modules.disabling.database import set_command_state
from korone.utils.i18n import gettext as _


class EnableHandler(MessageHandler):
    @staticmethod
    @router.message(Command("enable", disableable=False) & IsGroupChat & IsAdmin)
    async def enable(client: Client, message: Message) -> None:
        command = CommandObject(message).parse()
        if not command.args:
            await message.reply(_("You need to specify a command to enable."))
            return

        args = command.args.split(" ")
        if len(args) > 1:
            await message.reply(_("You can only enable one command at a time."))
            return

        command = args[0]
        if command not in COMMANDS:
            await message.reply(
                _(
                    "Unknown command to disable:\n"
                    "- <code>{command}</code>\n"
                    "Check the /disableable!"
                ).format(command=command)
            )
            return

        cmd_db = await fetch_command_state(command)

        if cmd_db and bool(cmd_db[0]["state"]):
            await message.reply(_("This command is already enabled."))
            return

        await set_command_state(message.chat.id, command, state=True)

        await message.reply(_("Command enabled."))

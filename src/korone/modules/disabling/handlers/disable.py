# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.handlers.abstract.message_handler import MessageHandler
from korone.modules.core import check_command_state
from korone.modules.disabling.database import set_command_state
from korone.modules.utils.filters import Command
from korone.modules.utils.filters.command import CommandObject
from korone.utils.i18n import gettext as _


class DisableHandler(MessageHandler):
    @staticmethod
    @router.message(Command("disable"))
    async def handle(client: Client, message: Message) -> None:
        command = CommandObject(message).parse()
        if not command.args:
            await message.reply(_("You need to specify a command to disable."))
            return

        args = command.args.split(" ")
        if len(args) > 1:
            await message.reply(_("You can only disable one command at a time."))
            return

        command_to_disable = args[0]
        if command_to_disable == command.command:
            await message.reply(_("You can't disable the command that disables commands."))
            return

        cmd_db = await check_command_state(command_to_disable)

        if cmd_db and bool(cmd_db[0]["state"]) is False:
            await message.reply(_("This command is already disabled."))
            return

        await set_command_state(message.chat.id, command_to_disable, state=False)
        await message.reply(_("Command disabled."))

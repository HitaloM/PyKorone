# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.handlers.abstract.message_handler import MessageHandler
from korone.modules.core import check_command_state
from korone.modules.disabling.database import set_command_state
from korone.modules.utils.filters import Command, CommandObject, IsAdmin
from korone.utils.i18n import gettext as _


class EnableHandler(MessageHandler):
    @staticmethod
    @router.message(Command("enable") & IsAdmin)
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
        cmd_db = await check_command_state(command)

        if not cmd_db:
            await message.reply(_("This command is not disabled."))
            return

        if bool(cmd_db[0]["state"]) is True:
            await message.reply(_("This command is already enabled."))
            return

        await set_command_state(message.chat.id, command, state=True)
        await message.reply(_("Command enabled."))

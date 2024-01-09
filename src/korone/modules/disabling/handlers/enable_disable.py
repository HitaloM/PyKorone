# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client, filters
from hydrogram.types import Message

from korone.database.impl import SQLite3Connection
from korone.database.query import Query
from korone.database.table import Document
from korone.decorators import on_message
from korone.handlers.message_handler import MessageHandler
from korone.modules.core import COMMANDS
from korone.utils.commands import get_command_arg
from korone.utils.i18n import gettext as _


class CommandHandler(MessageHandler):
    @staticmethod
    async def check_command(command: str, message: Message) -> bool:
        if command == "":
            await message.reply_text(_("Give me a command."))
            return False

        if command not in COMMANDS:
            await message.reply_text(_("This command does not exist in the bot!"))
            return False

        return True

    @staticmethod
    async def toggle(command: str, chat_id: int, state: bool) -> None:
        if command not in COMMANDS:
            raise KeyError(f"Command '{command}' has not been registered!")

        if "parent" in COMMANDS[command]:
            command = COMMANDS[command]["parent"]

        COMMANDS[command]["chat"][chat_id] = state

        async with SQLite3Connection() as conn:
            table = await conn.table("DisabledCommands")
            query = Query()
            query = query.chat_id == chat_id
            if await table.query(query):
                await table.update(Document(state=state), query)
                return

            await table.insert(Document(chat_id=chat_id, command=command, state=state))


class EnableCommand(CommandHandler):
    @on_message(filters.command("enable"))
    async def handle(self, client: Client, message: Message) -> None:
        command = get_command_arg(message)

        if not await self.check_command(command, message):
            return

        try:
            await self.toggle(command, message.chat.id, True)
        except KeyError:
            await message.reply_text(_("Invalid command!"))
            return

        await message.reply_text(_("Command enabled!"))


class DisableCommand(CommandHandler):
    @on_message(filters.command("disable"))
    async def handle(self, client: Client, message: Message) -> None:
        command = get_command_arg(message)

        if command in ["disable", "enable"]:
            await message.reply_text(_("You cannot disable this command!"))
            return

        if not await self.check_command(command, message):
            return

        try:
            await self.toggle(command, message.chat.id, False)
        except KeyError:
            await message.reply_text(_("Invalid command!"))
            return

        await message.reply_text(_("Command disabled!"))

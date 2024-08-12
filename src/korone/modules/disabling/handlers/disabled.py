# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, IsAdmin, IsGroupChat
from korone.handlers.abstract import MessageHandler
from korone.modules.disabling.database import get_disabled_commands
from korone.utils.i18n import gettext as _


class DisabledHandler(MessageHandler):
    @staticmethod
    @router.message(Command("disabled", disableable=False) & IsGroupChat & IsAdmin)
    async def handle(client: Client, message: Message) -> None:
        chat_id = message.chat.id

        disabled_commands = await get_disabled_commands(chat_id)
        if not disabled_commands:
            await message.reply(_("No commands are disabled in this chat."))
            return

        disabled_commands = sorted(disabled_commands)

        text = _("The following commands are disabled in this chat:\n")
        for command in disabled_commands:
            text += f"- <code>{command}</code>\n"

        await message.reply(text)

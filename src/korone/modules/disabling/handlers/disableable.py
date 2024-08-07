# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, IsAdmin
from korone.handlers.abstract import MessageHandler
from korone.modules import COMMANDS
from korone.utils.i18n import gettext as _


class ListDisableableHandler(MessageHandler):
    @staticmethod
    @router.message(Command("disableable", disableable=False) & IsAdmin)
    async def handle(client: Client, message: Message) -> None:
        disableable = sorted([
            command for command in COMMANDS if "parent" not in COMMANDS[command]
        ])

        text = _("The following commands can be disabled:\n")
        for command in disableable:
            text += f"- <code>{command}</code>\n"

        await message.reply(text)

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client, filters
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, IsAdmin
from korone.handlers.abstract import MessageHandler
from korone.modules.disabling.database import disabled_commands
from korone.utils.i18n import gettext as _


class DisabledHandler(MessageHandler):
    @staticmethod
    @router.message(Command("disabled", disableable=False) & ~filters.private & IsAdmin)
    async def handle(client: Client, message: Message) -> None:
        chat_id = message.chat.id
        disabled = await disabled_commands(chat_id)
        if not disabled:
            await message.reply(_("No commands are disabled in this chat."))
            return

        text = _("The following commands are disabled in this chat:\n")
        for command in disabled:
            text += f"- <code>{command}</code>\n"

        await message.reply(text)

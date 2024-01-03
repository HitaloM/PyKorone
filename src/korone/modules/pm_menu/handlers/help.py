# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from hairydogm.i18n import gettext as _
from hydrogram import Client, filters
from hydrogram.types import Message
from korone.decorators import on_message
from korone.decorators.i18n import use_gettext
from korone.handlers.message_handler import MessageHandler


class HelpHandler(MessageHandler):
    @use_gettext
    @on_message(filters.command("help"))
    async def handle(self, client: Client, message: Message):
        await message.reply_text(_("Hello, I'm Korone!"))

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client, filters
from hydrogram.types import Message
from korone.decorators.message import on_message
from korone.handlers import MessageHandler


class StartHandler(MessageHandler):
    @on_message(filters.command("start"))
    async def handle(self, client: Client, message: Message):
        await message.reply_text("Hello, I'm Korone!")

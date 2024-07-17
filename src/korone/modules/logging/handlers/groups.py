# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import textwrap

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client, filters
from hydrogram.enums import ChatType
from hydrogram.errors import BadRequest
from hydrogram.types import InlineKeyboardMarkup, Message

from korone import constants
from korone.decorators import router
from korone.handlers.abstract import MessageHandler
from korone.utils.logging import logger


class LogGroup(MessageHandler):
    WELCOME_TEXT = textwrap.dedent("""\
        Welcome to PyKorone!

        Check out the documentation for more information on how to use me.
    """)

    @classmethod
    def build_keyboard(cls) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="Documentation", url=constants.DOCS_URL)
        keyboard.button(text="Channel", url=constants.TELEGRAM_URL)
        return keyboard.as_markup()

    @classmethod
    def build_log_text(cls, message: Message) -> str:
        username = f"@{message.chat.username}" if message.chat.username else "None"
        return (
            f"I was added to a group!\n"
            f"Title: {message.chat.title}\n"
            f"ID: <code>{message.chat.id}</code>\n"
            f"Username: {username}\n"
        )

    @router.message(filters.new_chat_members)
    async def handle(self, client: Client, message: Message) -> None:
        if not message.new_chat_members or message.chat.type == ChatType.CHANNEL:
            if message.chat.type == ChatType.CHANNEL:
                await client.leave_chat(chat_id=message.chat.id)
            return

        for member in message.new_chat_members:
            if member.id == client.me.id:  # type: ignore
                try:
                    await client.send_message(
                        chat_id=constants.LOGS_CHAT, text=self.build_log_text(message)
                    )
                except BadRequest:
                    await logger.aexception("[LogGroup] Failed to send log message to logs chat.")

                await message.reply(text=self.WELCOME_TEXT, reply_markup=self.build_keyboard())
                break

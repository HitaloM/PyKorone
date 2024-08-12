# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client, filters
from hydrogram.enums import ChatType
from hydrogram.errors import BadRequest
from hydrogram.types import InlineKeyboardMarkup, Message

from korone import constants
from korone.config import ConfigManager
from korone.decorators import router
from korone.handlers.abstract import MessageHandler
from korone.utils.logging import logger

LOGS_CHAT = ConfigManager().get("korone", "LOGS_CHAT")


class LogGroup(MessageHandler):
    @router.message(filters.new_chat_members)
    async def handle(self, client: Client, message: Message) -> None:
        if not message.new_chat_members or message.chat.type == ChatType.CHANNEL:
            if message.chat.type == ChatType.CHANNEL:
                await client.leave_chat(chat_id=message.chat.id)
            return

        for member in message.new_chat_members:
            if member.id == client.me.id:  # type: ignore
                await self.log_group_addition(client, message)
                await self.send_welcome_message(message)
                break

    @staticmethod
    def build_keyboard() -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="Documentation", url=constants.DOCS_URL)
        keyboard.button(text="Channel", url=constants.TELEGRAM_URL)
        return keyboard.as_markup()

    @staticmethod
    def build_log_text(message: Message) -> str:
        username = f"@{message.chat.username}" if message.chat.username else "None"
        return (
            f"I was added to a group!\n"
            f"Title: {message.chat.title}\n"
            f"ID: <code>{message.chat.id}</code>\n"
            f"Username: {username}\n"
        )

    async def log_group_addition(self, client: Client, message: Message) -> None:
        try:
            text = self.build_log_text(message)
            await client.send_message(chat_id=LOGS_CHAT, text=text)
        except BadRequest:
            await logger.aexception("[LogGroup] Failed to send log message to logs chat.")

    async def send_welcome_message(self, message: Message) -> None:
        text = (
            "Welcome to PyKorone!\n\n"
            "Check out the documentation for more information on how to use me."
        )
        keyboard = self.build_keyboard()
        await message.reply(text, reply_markup=keyboard)

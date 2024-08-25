# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from contextlib import suppress

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client, filters
from hydrogram.enums import ChatType
from hydrogram.errors import BadRequest
from hydrogram.types import Message

from korone import constants
from korone.config import ConfigManager
from korone.decorators import router

LOGS_CHAT = ConfigManager().get("korone", "LOGS_CHAT")


@router.message(filters.new_chat_members)
async def log_joined_groups(client: Client, message: Message) -> None:
    if not message.new_chat_members:
        return

    if message.chat.type == ChatType.CHANNEL:
        await client.leave_chat(chat_id=message.chat.id)
        return

    for member in message.new_chat_members:
        if member.id == client.me.id:  # type: ignore
            with suppress(BadRequest):
                username = f"@{message.chat.username}" if message.chat.username else "None"

                await client.send_message(
                    chat_id=LOGS_CHAT,
                    text=(
                        f"I was added to a group!\n"
                        f"Title: {message.chat.title}\n"
                        f"ID: <code>{message.chat.id}</code>\n"
                        f"Username: {username}\n"
                    ),
                )

            text = (
                "Welcome to PyKorone!\n\n"
                "Check out the documentation for more information on how to use me."
            )

            keyboard = InlineKeyboardBuilder()
            keyboard.button(text="📄 Documentation", url=constants.DOCS_URL)
            keyboard.button(text="📢 Channel", url=constants.TELEGRAM_URL)

            await message.reply(text, reply_markup=keyboard.as_markup())
            break

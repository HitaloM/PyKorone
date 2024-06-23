# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M.

from hydrogram import Client
from hydrogram.enums import ChatType
from hydrogram.types import Message

from korone.decorators import router
from korone.filters import Command, CommandObject
from korone.handlers.abstract import MessageHandler
from korone.modules.users_groups.database import get_chat_by_id, get_chat_by_username
from korone.utils.i18n import gettext as _


class GetChatHandler(MessageHandler):
    @staticmethod
    async def fetch_chat(message: Message, identifier: str | int) -> dict | None:
        try:
            if isinstance(identifier, str):
                if identifier.isdigit() or (
                    identifier.startswith("-100") and identifier[4:].isdigit()
                ):
                    chat_id = int(identifier)
                    chat = (await get_chat_by_id(chat_id))[0]
                elif identifier.startswith("@"):
                    username = identifier[1:]
                    chat = (await get_chat_by_username(username))[0]
                else:
                    return None
            else:
                chat_id = identifier
                chat = (await get_chat_by_id(chat_id))[0]
        except IndexError:
            return None
        return chat

    @staticmethod
    @router.message(Command("chat"))
    async def handle(client: Client, message: Message) -> None:
        command = CommandObject(message).parse()
        chat_identifier = command.args or message.chat.id

        chat = await GetChatHandler.fetch_chat(message, chat_identifier)
        if not chat:
            if not command.args and message.chat.type == ChatType.PRIVATE:
                await message.reply(_("You should provide a chat ID or username."))
                return

            await message.reply(
                _("Invalid chat ID or username.") if command.args else _("Chat not found.")
            )
            return

        text = _("<b>Chat info</b>:\n")
        text += _("<b>ID</b>: <code>{id}</code>\n").format(id=chat["id"])
        text += _("<b>Title</b>: {title}\n").format(title=chat["title"])
        if username := chat.get("username"):
            text += _("<b>Username</b>: @{username}\n").format(username=username)
        if chat_type := chat["type"]:
            text += _("<b>Type</b>: {type}\n").format(type=chat_type)

        await message.reply(text)

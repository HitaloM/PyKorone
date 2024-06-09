# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import re

from hydrogram import Client, filters
from hydrogram.enums import MessageEntityType
from hydrogram.errors import PeerIdInvalid
from hydrogram.types import Message, MessageEntity, User

from korone.decorators import router
from korone.handlers import MessageHandler
from korone.modules.afk.database import get_afk_reason, get_user, is_afk, set_afk
from korone.utils.i18n import gettext as _


class CheckAfk(MessageHandler):
    @staticmethod
    async def get_user(entity: MessageEntity, client: Client, message: Message) -> User | None:
        offset: int = entity.offset
        length: int = entity.length
        username: str = message.text[offset : offset + length]
        data = await get_user(username)

        if not data:
            return None

        chat_id = data[0]["id"]

        try:
            user: User = await client.get_chat(chat_id)  # type: ignore
        except PeerIdInvalid:
            return None

        return user

    async def handle_mentioned_users(self, client: Client, message: Message) -> None:
        if not message.entities:
            return

        for entity in message.entities:
            user: User | None = None
            if entity.type == MessageEntityType.MENTION:
                user = await self.get_user(entity, client, message)
            elif entity.type == MessageEntityType.TEXT_MENTION:
                user = entity.user

        if user is not None:
            await self.send_afk_message(user, message)

    async def handle_reply_to_message(self, message: Message) -> None:
        if not message.reply_to_message or not message.reply_to_message.from_user:
            return

        reply_user = message.reply_to_message.from_user
        await self.send_afk_message(reply_user, message)

    @staticmethod
    async def send_afk_message(user: User, message: Message) -> None:
        if not user or user.id == message.from_user.id or not await is_afk(user.id):
            return

        text = _("{user} is afk!").format(user=user.first_name)
        if reason := await get_afk_reason(user.id):
            text += _("\nReason: {reason}").format(reason=reason)

        await message.reply(text)

    @router.message(~filters.private & ~filters.bot, group=-2)
    async def handle(self, client: Client, message: Message) -> None:
        if message.from_user and message.text and re.findall(r"^\/\bafk\b", message.text):
            return

        if await is_afk(message.from_user.id):
            await set_afk(message.from_user.id, state=False)
            return

        await self.handle_mentioned_users(client, message)
        await self.handle_reply_to_message(message)

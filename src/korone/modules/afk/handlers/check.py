# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

import re

from hydrogram import Client, filters
from hydrogram.enums import MessageEntityType
from hydrogram.errors import PeerIdInvalid
from hydrogram.types import Message, User

from korone.database.impl import SQLite3Connection
from korone.database.query import Query
from korone.database.table import Documents
from korone.decorators import router
from korone.handlers.message_handler import MessageHandler
from korone.modules.afk.utils import is_afk, set_afk
from korone.utils.i18n import gettext as _


class CheckAfk(MessageHandler):
    @staticmethod
    async def get_user(username: str) -> Documents:
        async with SQLite3Connection() as conn:
            table = await conn.table("Users")
            query = Query()
            return await table.query(query.username == username[1:])

    @staticmethod
    async def get_afk_reason(user_id: int) -> Documents | None:
        async with SQLite3Connection() as conn:
            table = await conn.table("Afk")
            query = Query()
            doc = await table.query(query.id == user_id)
            return doc[0]["reason"] if doc else None

    @router.message(~filters.private & ~filters.bot & filters.all, group=-2)
    async def handle(self, client: Client, message: Message) -> None:
        if message.from_user and message.text and re.findall(r"^\/\bafk\b", message.text):
            return

        if await is_afk(message.from_user.id):
            await set_afk(message.from_user.id, state=False)
            return

        if message.entities:
            for ent in message.entities:
                user: User | None = None
                if ent.type == MessageEntityType.MENTION:
                    if data := (
                        await self.get_user(message.text[ent.offset : ent.offset + ent.length])
                    ):
                        try:
                            user = await client.get_chat(data[0]["id"])  # type: ignore
                        except PeerIdInvalid:
                            continue
                elif ent.type == MessageEntityType.TEXT_MENTION:
                    user = ent.user

                if user and user.id != message.from_user.id and await is_afk(user.id):
                    text = _("{user} is afk!").format(user=user.first_name)
                    if reason := await self.get_afk_reason(user.id):
                        text += _("\nReason: {reason}").format(reason=reason)
                    await message.reply(text)
                    return

        if (
            message.reply_to_message
            and message.reply_to_message.from_user
            and message.reply_to_message.from_user.id != message.from_user.id
            and await is_afk(message.reply_to_message.from_user.id)
        ):
            text = _("{user} is afk!").format(user=message.reply_to_message.from_user.first_name)
            if reason := await self.get_afk_reason(message.reply_to_message.from_user.id):
                text += _("\nReason: {reason}").format(reason=reason)
            await message.reply(text)
            return

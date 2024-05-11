# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram.types import CallbackQuery

from korone.database.impl import SQLite3Connection
from korone.database.query import Query
from korone.database.table import Document


async def set_chat_language(is_private: bool, callback: CallbackQuery, language: str) -> None:
    async with SQLite3Connection() as conn:
        table = await conn.table("Users" if is_private else "Groups")
        query = Query()

        await table.update(Document(language=language), query.id == callback.message.chat.id)

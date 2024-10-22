# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram.types import CallbackQuery

from korone.database.query import Query
from korone.database.table import Document
from korone.client import Korone


async def set_chat_language(client: Korone, is_private: bool, callback: CallbackQuery, language: str) -> None:
    table = await client.db_connection.table("Users" if is_private else "Groups")

    await table.update(Document(language=language), Query().id == callback.message.chat.id)

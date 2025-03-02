# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from korone.database.query import Query
from korone.database.sqlite import SQLite3Connection
from korone.database.table import Document


async def save_lastfm_user(user_id: int, username: str) -> None:
    async with SQLite3Connection() as conn:
        table = await conn.table("LastFM")

        if await table.query(Query().id == user_id):
            await table.update(Document(username=username), Query().id == user_id)
            return

        doc = Document(id=user_id, username=username)
        await table.insert(doc)


async def get_lastfm_user(user_id: int) -> str | None:
    async with SQLite3Connection() as conn:
        table = await conn.table("LastFM")

        user = await table.query(Query().id == user_id)
        return user[0]["username"] if user else None

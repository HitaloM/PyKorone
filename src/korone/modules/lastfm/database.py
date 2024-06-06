# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from korone.database.query import Query
from korone.database.sqlite import SQLite3Connection
from korone.database.table import Document


async def save_lastfm_user(user_id: int, username: str) -> None:
    async with SQLite3Connection() as conn:
        table = await conn.table("LastFM")
        query = Query()

        if await table.query(query.id == user_id):
            await table.update(Document(username=username), query.id == user_id)
            return

        doc = Document(id=user_id, username=username)
        await table.insert(doc)


async def get_lastfm_user(user_id: int) -> str | None:
    async with SQLite3Connection() as conn:
        table = await conn.table("LastFM")
        query = Query()

        user = await table.query(query.id == user_id)
        if not user:
            return None

        return user[0]["username"]

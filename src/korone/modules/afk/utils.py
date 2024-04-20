# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from korone.database.impl import SQLite3Connection
from korone.database.query import Query
from korone.database.table import Document


async def set_afk(user_id: int) -> None:
    async with SQLite3Connection() as conn:
        table = await conn.table("Afk")
        query = Query()
        if not await table.query(query.id == user_id):
            await table.insert(Document(id=user_id))
            return

        await table.delete(query.id == user_id)


async def is_afk(user_id: int) -> bool:
    async with SQLite3Connection() as conn:
        table = await conn.table("Afk")
        query = Query()
        return bool(await table.query(query.id == user_id))

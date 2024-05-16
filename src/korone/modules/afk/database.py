# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from korone.database.impl import SQLite3Connection
from korone.database.query import Query
from korone.database.table import Document, Documents


async def set_afk(user_id: int, state: bool, reason: str | None = None) -> None:
    async with SQLite3Connection() as conn:
        table = await conn.table("Afk")
        query = Query()

        reason = reason or ""

        if not await table.query(query.id == user_id):
            await table.insert(Document(id=user_id, state=state, reason=reason))
            return

        await table.update(Document(state=state, reason=reason), query.id == user_id)


async def is_afk(user_id: int) -> bool:
    async with SQLite3Connection() as conn:
        table = await conn.table("Afk")
        query = Query()
        doc = await table.query(query.id == user_id)

        return bool(doc[0]["state"]) if doc else False


async def get_afk_reason(user_id: int) -> Documents | None:
    async with SQLite3Connection() as conn:
        table = await conn.table("Afk")
        query = Query()
        doc = await table.query(query.id == user_id)

        return doc[0]["reason"] if doc else None


async def get_user(username: str) -> Documents:
    async with SQLite3Connection() as conn:
        table = await conn.table("Users")
        query = Query()

        return await table.query(query.username == username[1:])

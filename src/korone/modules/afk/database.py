# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from korone.database.query import Query
from korone.database.sqlite import SQLite3Connection
from korone.database.table import Document, Documents


async def set_afk(user_id: int, state: bool, reason: str | None = None) -> None:
    async with SQLite3Connection() as conn:
        table = await conn.table("Afk")

        reason = reason or ""

        if not await table.query(Query().id == user_id):
            await table.insert(Document(id=user_id, state=state, reason=reason))
            return

        await table.update(Document(state=state, reason=reason), Query().id == user_id)


async def is_afk(user_id: int) -> bool:
    async with SQLite3Connection() as conn:
        table = await conn.table("Afk")
        doc = await table.query(Query().id == user_id)

        return bool(doc[0]["state"]) if doc else False


async def get_afk_reason(user_id: int) -> str | None:
    async with SQLite3Connection() as conn:
        table = await conn.table("Afk")
        doc = await table.query(Query().id == user_id)

        return doc[0]["reason"] if doc else None


async def get_user(username: str) -> Documents:
    async with SQLite3Connection() as conn:
        table = await conn.table("Users")

        return await table.query(Query().username == username[1:])

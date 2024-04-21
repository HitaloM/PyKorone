# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from korone.database.impl import SQLite3Connection
from korone.database.query import Query
from korone.database.table import Document


async def set_afk(user_id: int, state: bool, reason: str | None = None) -> None:
    async with SQLite3Connection() as conn:
        table = await conn.table("Afk")
        query = Query()
        if reason is None:
            reason = ""
        if not await table.query(query.id == user_id):
            await table.insert(Document(id=user_id, state=state, reason=reason))
            return

        await table.update(Document(state=state, reason=reason), query.id == user_id)


async def is_afk(user_id: int) -> bool:
    async with SQLite3Connection() as conn:
        table = await conn.table("Afk")
        query = Query()
        doc = await table.query(query.id == user_id)
        if not doc:
            return False

        return bool(doc[0]["state"])

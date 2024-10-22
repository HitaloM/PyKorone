# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from korone.database.query import Query
from korone.database.table import Document, Documents
from korone.client import Korone

async def set_afk(client: Korone, user_id: int, state: bool, reason: str | None = None) -> None:
    table = await client.db_connection.table("Afk")

    reason = reason or ""

    if not await table.query(Query().id == user_id):
        await table.insert(Document(id=user_id, state=state, reason=reason))
        return

    await table.update(Document(state=state, reason=reason), Query().id == user_id)


async def is_afk(client: Korone, user_id: int) -> bool:
    table = await client.db_connection.table("Afk")
    doc = await table.query(Query().id == user_id)

    return bool(doc[0]["state"]) if doc else False


async def get_afk_reason(client: Korone, user_id: int) -> str | None:
    table = await client.db_connection.table("Afk")
    doc = await table.query(Query().id == user_id)

    return doc[0]["reason"] if doc else None


async def get_user(client: Korone, username: str) -> Documents:
    table = await client.db_connection.table("Users")

    return await table.query(Query().username == username[1:])

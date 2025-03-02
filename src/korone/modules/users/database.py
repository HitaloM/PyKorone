# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from korone.database.query import Query
from korone.database.sqlite import SQLite3Connection
from korone.database.table import Documents


async def get_user_by_id(user_id: int) -> Documents:
    async with SQLite3Connection() as conn:
        table = await conn.table("Users")
        return await table.query(Query().id == user_id)


async def get_user_by_username(username: str) -> Documents:
    async with SQLite3Connection() as conn:
        table = await conn.table("Users")
        return await table.query(Query().username == username.lower())

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from korone.database.query import Query
from korone.database.table import Documents
from korone.client import Korone


async def get_user_by_id(client: Korone, user_id: int) -> Documents:
    table = await client.db_connection.table("Users")
    return await table.query(Query().id == user_id)


async def get_user_by_username(client: Korone, username: str) -> Documents:
    table = await client.db_connection.table("Users")
    return await table.query(Query().username == username.lower())

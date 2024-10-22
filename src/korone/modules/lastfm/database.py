# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from korone.database.query import Query
from korone.database.table import Document
from korone.client import Korone


async def save_lastfm_user(client: Korone, user_id: int, username: str) -> None:
    table = await client.db_connection.table("LastFM")

    if await table.query(Query().id == user_id):
        await table.update(Document(username=username), Query().id == user_id)
        return

    doc = Document(id=user_id, username=username)
    await table.insert(doc)


async def get_lastfm_user(client: Korone, user_id: int) -> str | None:
    table = await client.db_connection.table("LastFM")

    user = await table.query(Query().id == user_id)
    return user[0]["username"] if user else None

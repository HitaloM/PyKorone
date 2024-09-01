# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from korone.database.query import Query
from korone.database.sqlite import SQLite3Connection
from korone.database.table import Document, Documents


async def get_or_create_pack(user_id: int, pack_type: str) -> Documents:
    async with SQLite3Connection() as conn:
        table = await conn.table("StickerPack")
        query = (Query().user_id == user_id) & (Query().type == pack_type)

        if result := await table.query(query):
            return result

        await table.insert(Document(user_id=user_id, type=pack_type, num=1))
        return await table.query(query)


async def update_user_pack(user_id: int, pack_type: str, num: int) -> None:
    async with SQLite3Connection() as conn:
        table = await conn.table("StickerPack")
        query = (Query().user_id == user_id) & (Query().type == pack_type)
        await table.update(Document(num=num), query)

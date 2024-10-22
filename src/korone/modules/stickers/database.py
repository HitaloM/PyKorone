# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from korone.database.query import Query
from korone.database.table import Document, Documents
from korone.client import Korone


async def get_or_create_pack(client: Korone, user_id: int, pack_type: str) -> Documents:
    table = await client.db_connection.table("StickerPack")
    query = (Query().user_id == user_id) & (Query().type == pack_type)

    if result := await table.query(query):
        return result

    await table.insert(Document(user_id=user_id, type=pack_type, num=1))
    return await table.query(query)


async def update_user_pack(client: Korone, user_id: int, pack_type: str, num: int) -> None:
    table = await client.db_connection.table("StickerPack")
    query = (Query().user_id == user_id) & (Query().type == pack_type)
    await table.update(Document(num=num), query)

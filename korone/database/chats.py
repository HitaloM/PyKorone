# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

from sqlite3 import Row
from time import time
from typing import Dict, Iterable, Optional

from .core import database

conn = database.get_conn()


async def get_chat_by_id(id: int) -> Optional[Row]:
    cursor = await conn.execute("SELECT * FROM chats WHERE id = ?", (id,))
    row = await cursor.fetchone()
    await cursor.close()
    return row


async def filter_chats_by_language(language: str) -> Iterable[Row]:
    cursor = await conn.execute("SELECT * FROM chats WHERE language = ?", (language,))
    row = await cursor.fetchall()
    await cursor.close()
    return row


async def register_chat_by_dict(info: Dict) -> Optional[Row]:
    id = info["id"]

    await conn.execute(
        "INSERT INTO chats (id, registration_time) VALUES (?, ?)", (id, time())
    )
    if conn.total_changes <= 0:
        raise AssertionError
    await conn.commit()

    return await get_chat_by_id(id)

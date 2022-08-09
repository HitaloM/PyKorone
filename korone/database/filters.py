# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

from sqlite3 import Row
from typing import Iterable

from .core import database

conn = database.get_conn()


async def add_filter(
    chat_id: int, handler: str, raw_data: str, file_id: int, filter_type: str
):
    await conn.execute(
        "INSERT INTO filters(chat_id, handler, data, file_id, filter_type) VALUES(?, ?, ?, ?, ?)",
        (chat_id, handler, raw_data, file_id, filter_type),
    )
    await conn.commit()


async def update_filter(
    chat_id: int, handler: str, data: str, file_id: int, filter_type: str
):
    await conn.execute(
        "UPDATE filters SET data = ?, file_id = ?, filter_type = ? WHERE chat_id = ? AND handler = ?",
        (data, file_id, filter_type, chat_id, handler),
    )
    await conn.commit()


async def remove_filter(chat_id: int, handler: str):
    await conn.execute(
        "DELETE from filters WHERE chat_id = ? AND handler = ?", (chat_id, handler)
    )
    await conn.commit()


async def get_all_filters(chat_id: int) -> Iterable[Row]:
    cursor = await conn.execute("SELECT * FROM filters WHERE chat_id = ?", (chat_id,))
    row = await cursor.fetchall()
    return row

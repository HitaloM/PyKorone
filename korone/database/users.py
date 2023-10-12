# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo M. <https://github.com/HitaloM>

import time
from collections.abc import Iterable
from sqlite3 import Row

from .core import database

conn = database.get_conn()


async def get_user_by_id(id: int) -> Row | None:
    cursor = await conn.execute("SELECT * FROM users WHERE id = ?", (id,))
    row = await cursor.fetchone()
    await cursor.close()
    return row


async def filter_users_by_language(language: str) -> Iterable[Row]:
    cursor = await conn.execute("SELECT * FROM users WHERE language = ?", (language,))
    row = await cursor.fetchall()
    await cursor.close()
    return row


async def register_user_by_dict(info: dict) -> Row | None:
    id, language = info["id"], info["language_code"].split("-")[0]

    await conn.execute(
        "INSERT INTO users (id, language, registration_time) VALUES (?, ?, ?)",
        (id, language, time.time()),
    )
    if conn.total_changes <= 0:
        raise AssertionError
    await conn.commit()

    return await get_user_by_id(id)

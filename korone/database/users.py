# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

import time
from sqlite3 import Row
from typing import Dict, Iterable, Optional

from .core import database

conn = database.get_conn()


async def get_user_by_id(id: int) -> Optional[Row]:
    cursor = await conn.execute("SELECT * FROM users WHERE id = ?", (id,))
    row = await cursor.fetchone()
    await cursor.close()
    return row


async def filter_users_by_language(language: str) -> Iterable[Row]:
    cursor = await conn.execute("SELECT * FROM users WHERE language = ?", (language,))
    row = await cursor.fetchall()
    await cursor.close()
    return row


async def register_user_by_dict(info: Dict) -> Optional[Row]:
    id, language = info["id"], info["language_code"]

    if language == "pt-br":
        language = "pt_BR"

    await conn.execute(
        "INSERT INTO users (id, language, registration_time) VALUES (?, ?, ?)",
        (id, language, time.time()),
    )
    if conn.total_changes <= 0:
        raise AssertionError
    await conn.commit()

    return await get_user_by_id(id)

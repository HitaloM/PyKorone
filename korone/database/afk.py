# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

from sqlite3 import Row
from time import time
from typing import Optional

from .core import database

conn = database.get_conn()


async def set_afk(user_id: int, reason: str):
    await conn.execute(
        "INSERT INTO afk(user_id, reason, time) VALUES(?, ?, ?)",
        (user_id, reason, time()),
    )
    await conn.commit()


async def rm_afk(user_id: int) -> bool:
    cursor = await conn.execute("DELETE FROM afk WHERE user_id = ?", (user_id,))
    if cursor.rowcount == 0:
        return False
    await conn.commit()
    return True


async def is_afk(user_id: int) -> Optional[Row]:
    cursor = await conn.execute("SELECT * FROM afk WHERE user_id = ?", (user_id,))
    row = await cursor.fetchone()
    return row

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

from sqlite3 import Row
from typing import Iterable

from .core import database

conn = database.get_conn()


async def disable_command(chat_id: int, command: str) -> None:
    await conn.execute(
        "INSERT INTO disabled (chat_id, disabled_cmd) VALUES (?, ?)",
        (chat_id, command),
    )
    if conn.total_changes <= 0:
        raise AssertionError
    await conn.commit()


async def enable_command(chat_id: int, command: str) -> None:
    await conn.execute(
        "DELETE FROM disabled WHERE chat_id = ? AND disabled_cmd = ?",
        (chat_id, command),
    )
    if conn.total_changes <= 0:
        raise AssertionError
    await conn.commit()


async def is_cmd_disabled(chat_id: int, command: str) -> bool:
    cursor = await conn.execute(
        "SELECT * FROM disabled WHERE chat_id = ? AND disabled_cmd = ?",
        (chat_id, command),
    )
    row = await cursor.fetchone()
    return bool(row)


async def get_disabled_cmds(chat_id: int) -> Iterable[Row]:
    cursor = await conn.execute("SELECT * FROM disabled WHERE chat_id = ?", (chat_id,))
    row = await cursor.fetchall()
    return row

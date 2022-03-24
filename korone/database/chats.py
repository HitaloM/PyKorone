# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2021 Amano Team
#
# This file is part of Korone (Telegram Bot)

from time import time
from typing import Dict, Optional

from .core import database

conn = database.get_conn()


async def get_chat_by_id(id: int) -> Optional[Dict]:
    cursor = await conn.execute("SELECT * FROM chats WHERE id = ?", (id,))
    row = await cursor.fetchone()
    await cursor.close()
    return row


async def register_chat_by_dict(info: Dict) -> Dict:
    id = info["id"]

    await conn.execute(
        "INSERT INTO chats (id, registration_time) VALUES (?, ?)", (id, time())
    )
    assert conn.total_changes > 0
    await conn.commit()

    return await get_chat_by_id(id)

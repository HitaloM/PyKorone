# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2021 Amano Team
#
# This file is part of Korone (Telegram Bot)

import time
from typing import Dict, Optional

from .core import database

conn = database.get_conn()


async def get_user_by_id(id: int) -> Optional[Dict]:
    cursor = await conn.execute("SELECT * FROM users WHERE id = ?", (id,))
    row = await cursor.fetchone()
    await cursor.close()
    return row


async def register_user_by_dict(info: Dict) -> Dict:
    id, language = info["id"], info["language_code"]

    if language == "pt-br":
        language = "pt_BR"

    await conn.execute(
        "INSERT INTO users (id, language, registration_time) VALUES (?, ?, ?)",
        (id, language, time.time()),
    )
    assert conn.total_changes > 0
    await conn.commit()

    return await get_user_by_id(id)

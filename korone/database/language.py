# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2021 Amano Team
#
# This file is part of Korone (Telegram Bot)

from .core import database

conn = database.get_conn()


async def update_chat_language(id: int, language_code: str):
    await conn.execute(
        "UPDATE chats SET language = ? WHERE id = ?", (language_code, id)
    )
    await conn.commit()


async def update_user_language(id: int, language_code: str):
    await conn.execute(
        "UPDATE users SET language = ? WHERE id = ?", (language_code, id)
    )
    await conn.commit()

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

from .core import database

conn = database.get_conn()


async def change_chat_lang(id: int, language_code: str):
    await conn.execute(
        "UPDATE chats SET language = ? WHERE id = ?", (language_code, id)
    )
    await conn.commit()


async def change_user_lang(id: int, language_code: str):
    await conn.execute(
        "UPDATE users SET language = ? WHERE id = ?", (language_code, id)
    )
    await conn.commit()

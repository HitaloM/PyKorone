# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2022 Amano Team
#
# This file is part of Korone (Telegram Bot)

from korone.database.chats import get_chat_by_id
from korone.database.users import get_user_by_id
from korone.utils.langs import chat_languages, user_languages


async def get_user_lang(user_id: int) -> str:
    if user_id not in user_languages:
        user = await get_user_by_id(user_id)
        userlang = user_languages[user_id] = "en" if user is None else user["language"]
    else:
        userlang = None
    return userlang


async def get_chat_lang(chat_id: int) -> str:
    if chat_id not in chat_languages:
        chat = await get_chat_by_id(chat_id)
        chatlang = chat_languages[chat_id] = "en" if chat is None else chat["language"]
    else:
        chatlang = None
    return chatlang

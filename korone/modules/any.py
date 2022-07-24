# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

from pyrogram.enums import ChatType
from pyrogram.types import CallbackQuery, InlineQuery, Message

from korone.bot import Korone
from korone.database.chats import get_chat_by_id, register_chat_by_dict
from korone.database.users import get_user_by_id, register_user_by_dict


@Korone.on_message(group=-1)
async def check_chat(bot: Korone, message: Message):
    chat = message.chat
    user = message.from_user
    if not user:
        return

    if chat.type == ChatType.PRIVATE and await get_user_by_id(user.id) is None:
        await register_user_by_dict(user.__dict__)
    if (
        chat.type in (ChatType.GROUP, ChatType.SUPERGROUP)
        and await get_chat_by_id(chat.id) is None
    ):
        await register_chat_by_dict(chat.__dict__)


@Korone.on_callback_query(group=-1)
async def set_language_callback(bot: Korone, callback: CallbackQuery):
    chat = callback.message.chat
    user = callback.from_user
    if not user:
        return

    if chat.type == ChatType.PRIVATE and await get_user_by_id(user.id) is None:
        await register_user_by_dict(user.__dict__)
    if (
        chat.type in (ChatType.GROUP, ChatType.SUPERGROUP)
        and await get_chat_by_id(chat.id) is None
    ):
        await register_chat_by_dict(chat.__dict__)


@Korone.on_inline_query(group=-1)
async def set_language_inline_query(bot: Korone, inline_query: InlineQuery):
    user = inline_query.from_user
    if not user:
        return

    if await get_user_by_id(user.id) is None:
        await register_user_by_dict(user.__dict__)


@Korone.on_edited_message(group=-1)
async def edited(bot: Korone, message: Message):
    message.stop_propagation()

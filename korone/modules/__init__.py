# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo M. <https://github.com/HitaloM>

import html

from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import CallbackQuery, InlineQuery, Message

from ..bot import Korone
from ..database.chats import get_chat_by_id, register_chat_by_dict
from ..database.users import get_user_by_id, register_user_by_dict


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


@Korone.on_message(filters.new_chat_members)
async def log_added(bot: Korone, message: Message):
    if bot.me.id in [x.id for x in message.new_chat_members]:
        await bot.send_message(
            chat_id=message.chat.id,
            text="Thanks for adding me in your group!",
            disable_notification=True,
        )
        await bot.log(
            text=(
                f"I was added to the group <b>{html.escape(message.chat.title)}</b>"
                f" (<code>{message.chat.id}</code>)."
            ),
            disable_notification=False,
            disable_web_page_preview=True,
        )

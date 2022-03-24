# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2022 Amano Team
#
# This file is part of Korone (Telegram Bot)

import html

from pyrogram import filters
from pyrogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Message,
)

from korone.database.chats import get_chat_by_id, register_chat_by_dict
from korone.database.users import get_user_by_id, register_user_by_dict
from korone.korone import Korone
from korone.utils.langs.decorators import use_chat_language


@Korone.on_message(filters.edited, group=-5)
async def reject_edited(c: Korone, m: Message):
    m.stop_propagation()


@Korone.on_message(group=-2)
async def check_chat(c: Korone, m: Message):
    if m.chat.type == "private" and await get_user_by_id(m.from_user.id) is None:
        await register_user_by_dict(m.from_user.__dict__)
    if (
        m.chat.type in ["group", "supergroup"]
        and await get_chat_by_id(m.chat.id) is None
    ):
        await register_chat_by_dict(m.chat.__dict__)


@Korone.on_message(filters.new_chat_members & filters.group)
@use_chat_language()
async def thanks_for(c: Korone, m: Message):
    if c.me.id in [x.id for x in m.new_chat_members]:
        lang = m._lang
        if await get_chat_by_id(m.chat.id) is None:
            await register_chat_by_dict(m.chat.__dict__)

        await c.send_message(
            chat_id=m.chat.id,
            text=lang.thanks_for_add,
            disable_notification=True,
        )
        await c.send_log(
            text=(
                f"I've been added to the group <b>{html.escape(m.chat.title)}</b>"
                f" (<code>{m.chat.id}</code>)."
            ),
            disable_notification=False,
            disable_web_page_preview=True,
        )


@Korone.on_inline_query()
async def inline_help(c: Korone, q: InlineQuery):
    articles = [
        InlineQueryResultArticle(
            title="Informações",
            input_message_content=InputTextMessageContent(
                f"<b>Uso:</b> <code>@{c.me.username} user</code> - Exibe informações sobre você."
            ),
            description="Informações sobre você.",
            thumb_url="https://piics.ml/amn/eduu/info.png",
        ),
        InlineQueryResultArticle(
            title="Informações SpamWatch",
            input_message_content=InputTextMessageContent(
                f"<b>Uso:</b> <code>@{c.me.username} sw (id/username)</code> - Verifique se um usuário está banido no SpamWatch."
            ),
            description="Veja se um usuário está banido no SpamWatch.",
            thumb_url="https://telegra.ph/file/1c18bdedaf01664dc0029.png",
        ),
        InlineQueryResultArticle(
            title="Animes",
            input_message_content=InputTextMessageContent(
                f"<b>Uso:</b> <code>@{c.me.username} anime (pesquisa)</code> - Pesquise animes pelo inline."
            ),
            description="Pesquisa de animes com o Anilist.co.",
            thumb_url="https://telegra.ph/file/c41e41a22dcf6479137d0.png",
        ),
        InlineQueryResultArticle(
            title="Mangás",
            input_message_content=InputTextMessageContent(
                f"<b>Uso:</b> <code>@{c.me.username} manga (pesquisa)</code> - Pesquise mangás pelo inline."
            ),
            description="Pesquisa de mangás com o Anilist.co.",
            thumb_url="https://telegra.ph/file/c41e41a22dcf6479137d0.png",
        ),
    ]
    await q.answer(results=articles, cache_time=0)

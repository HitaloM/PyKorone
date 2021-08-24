# This file is part of Korone (Telegram Bot)
# Copyright (C) 2021 AmanoTeam

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import html

from pyrogram import filters
from pyrogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Message,
)

from korone.config import LOGS_CHANNEL
from korone.korone import Korone


@Korone.on_message(filters.new_chat_members)
async def thanks_for(c: Korone, m: Message):
    if c.me.id in [x.id for x in m.new_chat_members]:
        await c.send_message(
            chat_id=m.chat.id,
            text=(
                "Obrigado por me adicionar em seu grupo! "
                "Eu também possuo um grupo (@SpamTherapy) bem divertido"
                ", você está mais que convidado(a) a participar!"
            ),
            disable_notification=True,
        )
        await c.send_message(
            chat_id=LOGS_CHANNEL,
            text=(
                f"Eu fui adicionado ao grupo {html.escape(m.chat.title)}"
                f"<code>({m.chat.id})</code>."
            ),
            disable_notification=False,
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

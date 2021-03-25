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

import re
import html
import anilist
from typing import Dict, List

from pyrogram import Client, filters
from pyrogram.types import (
    Message,
    InlineQuery,
    InlineQueryResultArticle,
    InlineQueryResultPhoto,
    InputTextMessageContent,
)


@Client.on_inline_query(filters.regex(r"^user"))
async def user_inline(c: Client, q: InlineQuery):
    user = q.from_user

    text = "<b>Informações do usuário</b>:"
    text += f"\nID: <code>{user.id}</code>"
    text += f"\nNome: {html.escape(user.first_name)}"

    if user.last_name:
        text += f"\nSobrenome: {html.escape(user.last_name)}"

    if user.username:
        text += f"\nNome de Usuário: @{html.escape(user.username)}"

    text += f"\nLink de Usuário: {user.mention('link', style='html')}"

    await q.answer(
        [
            InlineQueryResultArticle(
                title="Informações",
                description="Exibe informações sobre você.",
                input_message_content=InputTextMessageContent(text),
            )
        ]
    )


@Client.on_inline_query(filters.regex(r"^anime"))
async def anime_inline(c: Client, q: InlineQuery):
    results: List[InlineQueryResultPhoto] = []
    query = q.query.split()
    search = " ".join(query[1:])
    async with anilist.AsyncClient() as client:
        results_search = await client.search(search, "anime", 10)
        for result in results_search:
            anime = await client.get(result.id, "anime")

            if len(anime.description) > 700:
                desc = f"{anime.description_short}..."
            else:
                desc = anime.description

            text = f"<b>{anime.title.romaji}</b> (<code>{anime.title.native}</code>)\n"
            text += f"<b>Tipo:</b> <code>{anime.format}</code>\n"
            if hasattr(anime, "status"):
                text += f"<b>Status:</b> <code>{anime.status}</code>\n"
            if hasattr(anime, "episodes"):
                text += f"<b>Episódios:</b> <code>{anime.episodes}</code>\n"
            if hasattr(anime, "duration"):
                text += f"<b>Duração:</b> <code>{anime.duration}</code> Por Ep.\n"
            if hasattr(anime.score, "average"):
                text += f"<b>Pontuação:</b> <code>{anime.score.average}</code>\n"
            if hasattr(anime, "genres"):
                text += f"<b>Gêneros:</b> <code>{', '.join(str(x) for x in anime.genres)}</code>\n"
            if hasattr(anime, "studios"):
                text += f"<b>Estúdios:</b> <code>{', '.join(str(x) for x in anime.studios)}</code>\n"
            text += f"\n<b>Descrição:</b> <i>{desc}</i>"

            keyboard = [[("Mais Info", anime.url, "url")]]

            try:
                keyboard[0].append(("Trailer 🎬", anime.trailer.url, "url"))
            except BaseException:
                pass

            if hasattr(anime, "banner"):
                photo = anime.banner

            results.append(
                InlineQueryResultPhoto(
                    photo_url=photo,
                    title=anime.title.romaji,
                    description=desc,
                    caption=text,
                    reply_markup=c.ikb(keyboard),
                )
            )
    if len(results) > 0:
        await q.answer(
            results=results,
            cache_time=3,
        )

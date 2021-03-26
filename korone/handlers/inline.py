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


@Client.on_inline_query()
async def on_inline(c: Client, q: InlineQuery):
    results: List[InlineQueryResultPhoto] = []
    query = q.query.split()
    if len(query) != 0 and query[0] == "anime":
        search = " ".join(query[1:])
        async with anilist.AsyncClient() as client:
            results_search = await client.search(search, "anime", 10)
            for result in results_search:
                anime = await client.get(result.id, "anime")

                if len(anime.description) > 700:
                    desc = f"{anime.description_short}..."
                else:
                    desc = anime.description

                text = (
                    f"<b>{anime.title.romaji}</b> (<code>{anime.title.native}</code>)\n"
                )
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
    elif len(query) != 0 and query[0] == "manga":
        search = " ".join(query[1:])
        async with anilist.AsyncClient() as client:
            results_search = await client.search(search, "manga", 10)
            for result in results_search:
                manga = await client.get(result.id, "manga")

                if len(manga.description) > 700:
                    desc = f"{manga.description_short}..."
                else:
                    desc = manga.description

                text = (
                    f"<b>{manga.title.romaji}</b> (<code>{manga.title.native}</code>)\n"
                )
                if hasattr(manga.start_date, "year"):
                    text += f"<b>Início:</b> <code>{manga.start_date.year}</code>\n"
                if hasattr(manga, "status"):
                    text += f"<b>Status:</b> <code>{manga.status}</code>\n"
                if hasattr(manga, "chapters"):
                    text += f"<b>Capítulos:</b> <code>{manga.chapters}</code>\n"
                if hasattr(manga, "volumes"):
                    text += f"<b>Volumes:</b> <code>{manga.volumes}</code>\n"
                if hasattr(manga.score, "average"):
                    text += f"<b>Pontuação:</b> <code>{manga.score.average}</code>\n"
                if hasattr(manga, "genres"):
                    text += f"<b>Gêneros:</b> <code>{', '.join(str(x) for x in manga.genres)}</code>\n"
                text += f"\n<b>Descrição:</b> <i>{desc}</i>"

                keyboard = [[("Mais Info", manga.url, "url")]]

                if hasattr(manga, "banner"):
                    photo = manga.banner

                results.append(
                    InlineQueryResultPhoto(
                        photo_url=photo,
                        title=manga.title.romaji,
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
    elif len(query) != 0 and query[0] == "user":
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
    else:
        articles = [
            InlineQueryResultArticle(
                title="Informações",
                input_message_content=InputTextMessageContent(
                    f"<b>Uso:</b> <code>@{c.me.username} user</code> - Exibe informações sobre você."
                ),
                description="Informações sobre você.",
                thumb_url="https://i.pinimg.com/originals/9e/1d/41/9e1d4160d3b2fd214c664ca1724fc4b4.png",
            ),
            InlineQueryResultArticle(
                title="Animes",
                input_message_content=InputTextMessageContent(
                    f"<b>Uso:</b> <code>@{c.me.username} anime</code> - Pesquise animes pelo inline."
                ),
                description="Pesquisa de animes com o Anilist.co.",
                thumb_url="https://i.pinimg.com/originals/9e/1d/41/9e1d4160d3b2fd214c664ca1724fc4b4.png",
            ),
            InlineQueryResultArticle(
                title="Mangás",
                input_message_content=InputTextMessageContent(
                    f"<b>Uso:</b> <code>@{c.me.username} manga</code> - Pesquise mangás pelo inline."
                ),
                description="Pesquisa de mangás com o Anilist.co.",
                thumb_url="https://i.pinimg.com/originals/9e/1d/41/9e1d4160d3b2fd214c664ca1724fc4b4.png",
            ),
        ]
        await q.answer(results=articles, cache_time=60)

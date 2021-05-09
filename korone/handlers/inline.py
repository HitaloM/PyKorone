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
from datetime import datetime
from typing import List

import anilist
from kantex.html import Bold, Code, KeyValueItem, Section, SubSection
from pyrogram import emoji
from pyrogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InlineQueryResultPhoto,
    InputTextMessageContent,
)

from korone.config import SW_API
from korone.handlers.utils.misc import cleanhtml
from korone.korone import Korone
from korone.utils import http


@Korone.on_inline_query()
async def on_inline(c: Korone, q: InlineQuery):
    results: List[InlineQueryResultPhoto] = []
    query = q.query.split()
    if len(query) != 0 and query[0] == "anime":
        search = " ".join(query[1:])
        async with anilist.AsyncClient() as client:
            results_search = await client.search(search, "anime", 10)
            for result in results_search:
                anime = await client.get(result.id, "anime")

                if hasattr(anime, "description"):
                    if len(anime.description) > 700:
                        desc = f"<b>Descrição curta:</b> {anime.description_short}[...]"
                    else:
                        desc = f"<b>Descrição:</b> {anime.description}"

                text = (
                    f"<b>{anime.title.romaji}</b> (<code>{anime.title.native}</code>)\n"
                )
                text += f"<b>ID:</b> <code>{anime.id}</code>\n"
                text += f"<b>Tipo:</b> <code>{anime.format}</code>\n"
                if hasattr(anime, "status"):
                    text += f"<b>Estado:</b> <code>{anime.status}</code>\n"
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
                if hasattr(anime, "description"):
                    text += f"\n<i>{desc}</i>"

                keyboard = [[("Mais informações", anime.url, "url")]]

                try:
                    keyboard[0].append(
                        (f"Trailer {emoji.CLAPPER_BOARD}", anime.trailer.url, "url")
                    )
                except BaseException:
                    pass

                keyboard.append(
                    [("Pesquisar mais", "anime", "switch_inline_query_current_chat")]
                )

                title = f"{anime.title.romaji} | {anime.format}"
                photo = f"https://img.anili.st/media/{anime.id}"

                results.append(
                    InlineQueryResultPhoto(
                        photo_url=photo,
                        title=title,
                        description=cleanhtml(desc),
                        caption=text,
                        reply_markup=c.ikb(keyboard),
                    )
                )
        if len(results) > 0:
            await q.answer(
                results=results,
                cache_time=0,
            )
    elif len(query) != 0 and query[0] == "manga":
        search = " ".join(query[1:])
        async with anilist.AsyncClient() as client:
            results_search = await client.search(search, "manga", 10)
            for result in results_search:
                manga = await client.get(result.id, "manga")

                if hasattr(manga, "description"):
                    if len(manga.description) > 700:
                        desc = f"<b>Descrição curta:</b> {manga.description_short}[...]"
                    else:
                        desc = f"<b>Descrição:</b> {manga.description}"

                text = (
                    f"<b>{manga.title.romaji}</b> (<code>{manga.title.native}</code>)\n"
                )
                text += f"<b>ID:</b> <code>{manga.id}</code>\n"
                if hasattr(manga.start_date, "year"):
                    text += f"<b>Início:</b> <code>{manga.start_date.year}</code>\n"
                if hasattr(manga, "status"):
                    text += f"<b>Estado:</b> <code>{manga.status}</code>\n"
                if hasattr(manga, "chapters"):
                    text += f"<b>Capítulos:</b> <code>{manga.chapters}</code>\n"
                if hasattr(manga, "volumes"):
                    text += f"<b>Volumes:</b> <code>{manga.volumes}</code>\n"
                if hasattr(manga.score, "average"):
                    text += f"<b>Pontuação:</b> <code>{manga.score.average}</code>\n"
                if hasattr(manga, "genres"):
                    text += f"<b>Gêneros:</b> <code>{', '.join(str(x) for x in manga.genres)}</code>\n"
                if hasattr(manga, "description"):
                    text += f"\n<i>{desc}</i>"

                keyboard = [
                    [
                        ("Mais Info", manga.url, "url"),
                        ("Pesquisar mais", "manga", "switch_inline_query_current_chat"),
                    ]
                ]

                photo = f"https://img.anili.st/media/{manga.id}"

                results.append(
                    InlineQueryResultPhoto(
                        photo_url=photo,
                        title=manga.title.romaji,
                        description=cleanhtml(desc),
                        caption=text,
                        reply_markup=c.ikb(keyboard),
                    )
                )
        if len(results) > 0:
            await q.answer(
                results=results,
                cache_time=0,
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
            ],
            cache_time=0,
        )
    elif len(query) != 0 and query[0] == "sw":
        args = " ".join(query[1:])
        try:
            if args:
                user = await c.get_users(f"{args}")
            else:
                user = q.from_user
        except BaseException as e:
            await q.answer(
                [
                    InlineQueryResultArticle(
                        title="Erro!",
                        description="Clique aqui para ver o erro.",
                        input_message_content=InputTextMessageContent(
                            f"<b>Erro:</b> <code>{e}</code>"
                        ),
                    )
                ],
                cache_time=0,
            )
            return

        r = await http.get(
            f"https://api.spamwat.ch/banlist/{int(user.id)}",
            headers={"Authorization": f"Bearer {SW_API}"},
        )
        spamwatch = Section(
            f"{user.mention(html.escape(user.first_name), style='html')}",
        )
        sw_ban = r.json()
        if r.status_code in [200, 404]:
            if r.status_code == 200:
                ban_message = sw_ban["message"]
                if ban_message:
                    ban_message = f'{ban_message[:128]}{"[...]" if len(ban_message) > 128 else ""}'
                spamwatch.extend(
                    [
                        SubSection(
                            "SpamWatch",
                            KeyValueItem(Bold("reason"), Code(sw_ban["reason"])),
                            KeyValueItem(
                                Bold("date"),
                                Code(datetime.fromtimestamp(sw_ban["date"])),
                            ),
                            KeyValueItem(Bold("timestamp"), Code(sw_ban["date"])),
                            KeyValueItem(Bold("admin"), Code(sw_ban["admin"])),
                            KeyValueItem(Bold("message"), Code(ban_message)),
                        ),
                    ]
                )
            elif r.status_code == 404:
                if sw_ban:
                    spamwatch.extend(
                        [
                            SubSection(
                                "SpamWatch",
                                KeyValueItem(Bold("banned"), Code("False")),
                            ),
                        ]
                    )
            await q.answer(
                [
                    InlineQueryResultArticle(
                        title=f"Sobre {html.escape(user.first_name)} - SpamWatch",
                        description="Veja se o usuário está banido no SpamWatch.",
                        input_message_content=InputTextMessageContent(spamwatch),
                    )
                ],
                cache_time=0,
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
                title="Informações SpamWatch",
                input_message_content=InputTextMessageContent(
                    f"<b>Uso:</b> <code>@{c.me.username} sw (id/username)</code> - Verifique se um usuário está banido no SpamWatch."
                ),
                description="Veja se um usuário está banido no SpamWatch.",
                thumb_url="https://i.pinimg.com/originals/9e/1d/41/9e1d4160d3b2fd214c664ca1724fc4b4.png",
            ),
            InlineQueryResultArticle(
                title="Animes",
                input_message_content=InputTextMessageContent(
                    f"<b>Uso:</b> <code>@{c.me.username} anime (pesquisa)</code> - Pesquise animes pelo inline."
                ),
                description="Pesquisa de animes com o Anilist.co.",
                thumb_url="https://i.pinimg.com/originals/9e/1d/41/9e1d4160d3b2fd214c664ca1724fc4b4.png",
            ),
            InlineQueryResultArticle(
                title="Mangás",
                input_message_content=InputTextMessageContent(
                    f"<b>Uso:</b> <code>@{c.me.username} manga (pesquisa)</code> - Pesquise mangás pelo inline."
                ),
                description="Pesquisa de mangás com o Anilist.co.",
                thumb_url="https://i.pinimg.com/originals/9e/1d/41/9e1d4160d3b2fd214c664ca1724fc4b4.png",
            ),
        ]
        await q.answer(results=articles, cache_time=60)

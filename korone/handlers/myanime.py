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

import time
import anilist
from jikanpy import AioJikan

from pyrogram import Client, filters
from pyrogram.types import Message

from korone.utils import http
from korone.handlers import COMMANDS_HELP
from korone.handlers.utils.image import pokemon_image_sync

GROUP = "animes"

COMMANDS_HELP[GROUP] = {
    "name": "Animes",
    "text": "O módulo dos Otakus!",
    "commands": {},
    "help": True,
}


def t(milliseconds: int) -> str:
    """Inputs time in milliseconds, to get beautified time,
    as string"""
    seconds, milliseconds = divmod(int(milliseconds), 1000)
    minutes, seconds = divmod(seconds, 60)
    hours, minutes = divmod(minutes, 60)
    days, hours = divmod(hours, 24)
    tmp = (
        ((str(days) + " Dias, ") if days else "")
        + ((str(hours) + " Horas, ") if hours else "")
        + ((str(minutes) + " Minutos, ") if minutes else "")
        + ((str(seconds) + " Segundos, ") if seconds else "")
        + ((str(milliseconds) + " ms, ") if milliseconds else "")
    )
    return tmp[:-2]


@Client.on_message(
    filters.cmd(
        command="anime (?P<search>.+)",
        action="Pesquise informações de animes pelo AniList.",
        group=GROUP,
    )
)
async def anilist_anime(c: Client, m: Message):
    query = m.matches[0]["search"]

    try:
        async with anilist.AsyncClient() as client:
            results = await client.search(query, "anime", 1)
            anime = await client.get(results[0].id, "anime")
    except IndexError:
        return await m.reply_text(
            "Algo deu errado, verifique sua pesquisa e tente novamente!"
        )

    if len(anime.description) > 700:
        desc = f"<b>Descrição:</b> <i>{anime.description_short}</i>..."
    else:
        desc = f"<b>Descrição:</b> <i>{anime.description}</i>"

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
        text += (
            f"<b>Gêneros:</b> <code>{', '.join(str(x) for x in anime.genres)}</code>\n"
        )
    if hasattr(anime, "studios"):
        text += f"<b>Estúdios:</b> <code>{', '.join(str(x) for x in anime.studios)}</code>\n"
    text += f"\n{desc}"

    keyboard = [[("Mais Info", anime.url, "url")]]

    try:
        keyboard[0].append(("Trailer 🎬", anime.trailer.url, "url"))
    except BaseException:
        pass

    await m.reply_photo(
        photo=f"https://img.anili.st/media/{anime.id}",
        caption=text,
        reply_markup=c.ikb(keyboard),
    )


@Client.on_message(
    filters.cmd(
        command="airing (?P<search>.+)",
        action="A próxima transmissão de um anime.",
        group=GROUP,
    )
)
async def anilist_airing(c: Client, m: Message):
    query = m.matches[0]["search"]

    try:
        async with anilist.AsyncClient() as client:
            results = await client.search(query, "anime", 1)
            anime = await client.get(results[0].id, "anime")
    except IndexError:
        return await m.reply_text(
            "Algo deu errado, verifique sua pesquisa e tente novamente!"
        )

    text = f"<b>{anime.title.romaji}</b> (<code>{anime.title.native}</code>)\n"
    text += f"<b>ID:</b> <code>{anime.id}</code>\n"
    text += f"<b>Tipo:</b> <code>{anime.format}</code>\n"
    if hasattr(anime, "next_airing"):
        airing_time = anime.next_airing.time_until * 1000
        text += f"<b>Episódio:</b> <code>{anime.next_airing.episode}</code>\n"
        text += f"<b>No ar em:</b> <code>{t(airing_time)}</code>"
    else:
        text += f"<b>Episódio:</b> <code>{anime.episodes}</code>\n"
        text += "<b>No ar em:</b> <code>N/A</code>"

    if hasattr(anime, "banner"):
        await m.reply_photo(photo=anime.banner, caption=text)
    else:
        await m.reply_text(text)


@Client.on_message(
    filters.cmd(
        command="manga (?P<search>.+)",
        action="Pesquise informações de mangás pelo AniList.",
        group=GROUP,
    )
)
async def anilist_manga(c: Client, m: Message):
    query = m.matches[0]["search"]

    try:
        async with anilist.AsyncClient() as client:
            results = await client.search(query, "manga", 1)
            manga = await client.get(results[0].id, "manga")
    except IndexError:
        return await m.reply_text(
            "Algo deu errado, verifique sua pesquisa e tente novamente!"
        )

    if len(manga.description) > 700:
        desc = f"<b>Descrição:</b> <i>{manga.description_short}</i>..."
    else:
        desc = f"<b>Descrição:</b> <i>{manga.description}</i>"

    text = f"<b>{manga.title.romaji}</b> (<code>{manga.title.native}</code>)\n"
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
        text += (
            f"<b>Gêneros:</b> <code>{', '.join(str(x) for x in manga.genres)}</code>\n"
        )
    text += f"\n{desc}"

    keyboard = [[("Mais Info", manga.url, "url")]]

    await m.reply_photo(
        photo=f"https://img.anili.st/media/{manga.id}",
        caption=text,
        reply_markup=c.ikb(keyboard),
    )


@Client.on_message(
    filters.cmd(
        command="upcoming",
        action="Veja os próximos animes a serem lançados.",
        group=GROUP,
    )
)
async def mal_upcoming(c: Client, m: Message):
    async with AioJikan() as jikan:
        pass

    upcoming = await jikan.top("anime", page=1, subtype="upcoming")
    await jikan.close()

    upcoming_list = [entry["title"] for entry in upcoming["top"]]
    upcoming_message = "<b>Próximos animes:</b>\n"

    for entry_num in range(len(upcoming_list)):
        if entry_num == 10:
            break
        upcoming_message += f"<b>{entry_num + 1}.</b> {upcoming_list[entry_num]}\n"

    await m.reply_text(upcoming_message)


@Client.on_message(
    filters.cmd(
        command="(?P<type>.*)pokemon (?P<search>.+)",
        action="Retorna o sprite do Pokémon específico, coloque 'back' antes de 'pokemon' para ver na visão traseira.",
        group=GROUP,
    )
)
async def poke_image(c: Client, m: Message):
    type = m.matches[0]["type"]
    text = m.matches[0]["search"]
    args = text.split()

    types = ["back", "front"]

    type = (type if type in types else "front") + "_"
    type += "_".join(args[1:]) if len(args) > 1 else "default"
    r = await http.get("https://pokeapi.co/api/v2/pokemon/" + args[0])
    if r.status_code == 200:
        sprites = (r.json())["sprites"]
        if type in sprites:
            sprite_url = sprites[type]
        else:
            await m.reply_text(
                f"<code>Error! Tipo \"{' '.join(args[1:])}\" não encontrado!</code>"
            )
            return
    else:
        await m.reply_text(f"<b>Error!</b>\n<code>{r.status_code}</code>")
        return

    if not sprite_url:
        await m.reply_text("Esse Pokémon não tem um sprite disponível!")
        return

    r = await http.get(sprite_url)
    if r.status_code == 200:
        sprite_io = r.read()
    else:
        await m.reply_text(f"<b>Error!</b>\n<code>{r.status_code}</code>")
        return

    await m.reply_document(document=pokemon_image_sync(sprite_io))


@Client.on_message(
    filters.cmd(
        command="pokeitem (?P<search>.+)",
        action="Retorna o sprite de um item Pokémon específico.",
        group=GROUP,
    )
)
async def poke_item_image(c: Client, m: Message):
    text = m.matches[0]["search"]
    args = text.split()

    type = "_".join(args[1:]) if len(args) > 1 else "default"
    r = await http.get("https://pokeapi.co/api/v2/item/" + args[0])
    if r.status_code == 200:
        sprites = (r.json())["sprites"]
        if type in sprites:
            sprite_url = sprites[type]
        else:
            await m.reply_text(
                f"<code>Error! Tipo \"{' '.join(args[1:])}\" não encontrado!</code>"
            )
    else:
        await m.reply_text(f"<b>Error!</b>\n<code>{r.status_code}</code>")
        return

    if not sprite_url:
        await m.reply_text("Esse item Pokémon não tem um sprite disponível!")
        return

    r = await http.get(sprite_url)
    if r.status_code == 200:
        sprite_io = r.read()
    else:
        await m.reply_text(f"<b>Error!</b>\n<code>{r.status_code}</code>")
        return

    await m.reply_document(document=pokemon_image_sync(sprite_io))

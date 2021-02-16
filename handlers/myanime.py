# This file is part of Korone (Telegram Bot)

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

import io
import time
import jikanpy
import aioanilist

from pyromod.helpers import ikb
from pyrogram import Client, filters
from pyrogram.types import Message
from PIL import Image

from utils import http
from . import COMMANDS_HELP

GROUP = "animes"

COMMANDS_HELP[GROUP] = {
    "name": "Animes",
    "text": "O módulo dos Otakus!",
    "commands": {},
    "help": True,
}


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
        async with aioanilist.Client() as client:
            results = await client.search("anime", query, limit=5)
            anime = await client.get("anime", results[0].id)
    except IndexError:
        return await m.reply_text(
            "Algo deu errado, verifique sua pesquisa e tente novamente!"
        )

    d = anime.description
    if len(d) > 700:
        d_short = d[0:500] + "..."
        desc = f"<b>Descrição:</b> {d_short}"
    else:
        desc = f"<b>Descrição:</b> {d}"

    text = f"<b>{anime.title.romaji}</b> (<code>{anime.title.native}</code>)\n"
    text += f"<b>Tipo:</b> <code>{anime.format}</code>\n"
    text += f"<b>Status:</b> <code>{anime.status}</code>\n"
    text += f"<b>Episódios:</b> <code>{anime.episodes}</code>\n"
    text += f"<b>Duração:</b> <code>{anime.duration}</code> Por Ep.\n"
    text += f"<b>Pontuação:</b> <code>{anime.score.average}</code>\n"
    text += f"<b>Gêneros:</b> <code>{', '.join(str(x) for x in anime.genres)}</code>\n"
    studio = ""
    for i in anime.studios.nodes:
        studio += i.name + ", "
    if len(studio) > 0:
        studio = studio[:-2]
    text += f"<b>Estúdios:</b> <code>{studio}</code>\n"
    text += f"\n{desc}"

    keyboard = [[("Mais Info", f"https://anilist.co/anime/{anime.id}", "url")]]

    try:
        keyboard[0].append(("Trailer 🎬", anime.trailer.url, "url"))
    except BaseException:
        pass

    await m.reply_photo(
        photo=f"https://img.anili.st/media/{anime.id}",
        caption=text,
        reply_markup=ikb(keyboard),
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
        async with aioanilist.Client() as client:
            results = await client.search("anime", query, limit=5)
            anime = await client.get("anime", results[0].id)
    except IndexError:
        return await m.reply_text(
            "Algo deu errado, verifique sua pesquisa e tente novamente!"
        )

    text = f"<b>{anime.title.romaji}</b> (<code>{anime.title.native}</code>)\n"
    text += f"<b>ID:</b> <code>{anime.id}</code>\n"
    text += f"<b>Tipo:</b> <code>{anime.format}</code>\n"
    if anime.next_airing:
        text += f"<b>No ar em:</b> <code>{time.strftime('%H:%M:%S - %d/%m/%Y', time.localtime(anime.next_airing.at))}</code>"
    else:
        text += "<b>No ar em:</b> <code>N/A</code>"

    if anime.banner:
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
        async with aioanilist.Client() as client:
            results = await client.search("manga", query, limit=5)
            manga = await client.get("manga", results[0].id)
    except IndexError:
        return await m.reply_text(
            "Algo deu errado, verifique sua pesquisa e tente novamente!"
        )

    d = manga.description
    if len(d) > 700:
        d_short = d[0:500] + "..."
        desc = f"<b>Descrição:</b> {d_short}"
    else:
        desc = f"<b>Descrição:</b> {d}"

    text = f"<b>{manga.title.romaji}</b> (<code>{manga.title.native}</code>)\n"
    if manga.start_date.year:
        text += f"<b>Início:</b> <code>{manga.start_date.year}</code>\n"
    text += f"<b>Status:</b> <code>{manga.status}</code>\n"
    if manga.chapters:
        text += f"<b>Capítulos:</b> <code>{manga.chapters}</code>\n"
    if manga.volumes:
        text += f"<b>Volumes:</b> <code>{manga.volumes}</code>\n"
    text += f"<b>Pontuação:</b> <code>{manga.score.average}</code>\n"
    text += f"<b>Gêneros:</b> <code>{', '.join(str(x) for x in manga.genres)}</code>\n"
    text += f"\n{desc}"

    keyboard = [[("Mais Info", f"https://anilist.co/manga/{manga.id}", "url")]]

    if manga.banner:
        await m.reply_photo(
            photo=f"https://img.anili.st/media/{manga.id}",
            caption=text,
            reply_markup=ikb(keyboard),
        )
    else:
        await m.reply_text(text)


@Client.on_message(
    filters.cmd(
        command="upcoming",
        action="Veja os próximos animes a serem lançados.",
        group=GROUP,
    )
)
async def mal_upcoming(c: Client, m: Message):
    jikan = jikanpy.jikan.Jikan()
    upcoming = jikan.top("anime", page=1, subtype="upcoming")

    upcoming_list = [entry["title"] for entry in upcoming["top"]]
    upcoming_message = "<b>Próximos animes:</b>\n"

    for entry_num in range(len(upcoming_list)):
        if entry_num == 10:
            break
        upcoming_message += f"<b>{entry_num + 1}.</b> {upcoming_list[entry_num]}\n"

    await m.reply_text(upcoming_message)


@Client.on_message(
    filters.cmd(
        command="pokemon (?P<search>.+)",
        action="Retornar o sprite do Pokémon específico.",
        group=GROUP,
    )
)
async def poke_image(c: Client, m: Message):
    text = m.matches[0]["search"]
    args = text.split()

    type = "front_"
    if len(args) > 1:
        type += "_".join(args[1:])
    else:
        type += "default"

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
        await m.reply_text(f"<code>Error! {r.status_code}</code>")
        return

    if not sprite_url:
        await m.reply_text("Esse Pokémon não tem um sprite disponível!")
        return

    r = await http.get(sprite_url)
    if r.status_code == 200:
        sprite_io = r.read()
    else:
        await m.reply_text(f"<code>Error! {r.status_code}</code>")
        return

    await m.reply_document(document=pokemon_image_sync(sprite_io))


def pokemon_image_sync(sprite_io):
    sticker_image = Image.open(io.BytesIO(sprite_io))
    sticker_image = sticker_image.crop(sticker_image.getbbox())

    final_width = 512
    final_height = 512

    if sticker_image.width > sticker_image.height:
        final_height = 512 * (sticker_image.height / sticker_image.width)
    elif sticker_image.width < sticker_image.height:
        final_width = 512 * (sticker_image.width / sticker_image.height)

    sticker_image = sticker_image.resize(
        (int(final_width), int(final_height)), Image.NEAREST
    )
    sticker_io = io.BytesIO()
    sticker_image.save(sticker_io, "WebP", quality=99)
    sticker_io.seek(0)
    sticker_io.name = "sticker.webp"

    return sticker_io

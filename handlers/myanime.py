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
import rapidjson as json
from anilistpy import Anime, animeSearch

from pyromod.helpers import ikb
from pyrogram import Client, filters
from pyrogram.types import Message
from urllib.parse import quote as urlencode
from PIL import Image

from utils import http


@Client.on_message(
    filters.cmd(
        command="mal (?P<search>.+)",
        action="Pesquise informações de animes pelo MyAnimeList.",
    )
)
async def animes(c: Client, m: Message):
    query = m.matches[0]["search"]
    query.replace("", "%20")
    surl = f"https://api.jikan.moe/v3/search/anime?q={urlencode(query)}"
    r = await http.get(surl)
    a = r.json()
    if "results" in a.keys():
        pic = f'{a["results"][0]["image_url"]}'
        text = f'<b>{a["results"][0]["title"]}</b>\n'
        text += f' • <b>Exibição:</b> <code>{a["results"][0]["airing"]}</code>\n'
        text += f' • <b>Tipo:</b> <code>{a["results"][0]["type"]}</code>\n'
        text += f' • <b>Episódios:</b> <code>{a["results"][0]["episodes"]}</code>\n'
        text += f' • <b>Pontuação:</b> <code>{a["results"][0]["score"]}</code>\n'
        text += f' • <b>Classificação:</b> <code>{a["results"][0]["rated"]}</code>\n\n'
        text += f'<b>Sinopse:</b>\n<i>{a["results"][0]["synopsis"]}</i>'
        await m.reply_photo(pic, caption=text)


@Client.on_message(
    filters.cmd(
        command="anilist (?P<search>.+)",
        action="Pesquise informações de animes pelo AniList.",
    )
)
async def anilist(c: Client, m: Message):
    query = m.matches[0]["search"]

    try:
        r = animeSearch(query)
        a_id = r.id(0)
        a = Anime(a_id)
    except BaseException as e:
        return await m.reply_text(f"Error! <code>{e}</code>")

    d = a.description()
    if len(d) > 700:
        d_short = d[0:500] + "..."
        desc = f"<b>Descrição:</b> {d_short}"
    else:
        desc = f"<b>Descrição:</b> {d}"

    g = a.genres()
    s = a.studios()
    try:
        text = f"<b>{r.title(0)}</b> (<code>{a.title('native')}</code>)\n"
        text += f"<b>Status:</b> <code>{a.status()}</code>\n"
        text += f"<b>Episódios:</b> <code>{a.episodes()}</code>\n"
        text += f"<b>Duração:</b> <code>{a.duration()}</code> Por Ep.\n"
        text += f"<b>Pontuação:</b> <code>{a.averageScore()}</code>\n"
        text += f"<b>Gêneros:</b> <code>{', '.join(str(x) for x in g)}</code>\n"
        text += f"<b>Estúdios:</b> <code>{', '.join(str(x) for x in s)}</code>\n"
        text += f"\n{desc}"
    except BaseException as e:
        return await m.reply_text(f"Error! <code>{e}</code>")

    await m.reply_photo(photo=f"https://img.anili.st/media/{a_id}", caption=text)


@Client.on_message(
    filters.cmd(
        command="pokemon (?P<search>.+)",
        action="Retornar o sprite do Pokémon específico.",
    )
)
async def poke_image(c: Client, m: Message):
    command = m.text.split()[0]
    text = m.matches[0]["search"]
    args = text.split()
    if not text:
        await m.reply_text("Specify a Pokémon name!")
        return

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

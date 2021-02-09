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

import rapidjson as json

from pyromod.helpers import ikb
from pyrogram import Client, filters
from pyrogram.types import Message
from urllib.parse import quote as urlencode

from utils import http


@Client.on_message(
    filters.cmd(
        command="sanime (?P<search>.+)",
        action="Pesquise informações de anime pelo MyAnimeList.",
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
        text += f' • <b>Airing:</b> <code>{a["results"][0]["airing"]}</code>\n'
        text += f' • <b>Type:</b> <code>{a["results"][0]["type"]}</code>\n'
        text += f' • <b>Episodes:</b> <code>{a["results"][0]["episodes"]}</code>\n'
        text += f' • <b>Score:</b> <code>{a["results"][0]["score"]}</code>\n'
        text += f' • <b>Rated:</b> <code>{a["results"][0]["rated"]}</code>\n\n'
        text += f'<b>Synopsis:</b>\n<i>{a["results"][0]["synopsis"]}</i>'
        await m.reply_photo(pic, caption=text)

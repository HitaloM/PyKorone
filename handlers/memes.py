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

import random
import rapidjson as json

from pyrogram import Client, filters
from pyrogram.types import Message

from utils import http
from handlers.utils.random import SHRUGS_REACT, REACTS

NEKO_URL = "https://nekos.life/api/v2/img/"


@Client.on_message(filters.cmd(command="hug", action="Dar um abraço."))
async def hug(c: Client, m: Message):
    r = await http.get(NEKO_URL + "hug")
    if r.status_code == 200:
        image_url = (r.json())["url"]
    else:
        return await m.reply_text(f"Erro!\n**{response.status}**")

    try:
        if m.reply_to_message:
            await m.reply_to_message.reply_document(document=image_url)
        else:
            await m.reply_document(document=image_url)
    except BaseException as e:
        return await m.reply_text(f"Erro!\n{e}")


@Client.on_message(filters.cmd(command="pat", action="Dar uma batida na cabeça."))
async def pat(c: Client, m: Message):
    r = await http.get(NEKO_URL + "pat")
    if r.status_code == 200:
        image_url = (r.json())["url"]
    else:
        return await m.reply_text(f"Erro!\n**{response.status}**")

    try:
        if m.reply_to_message:
            await m.reply_to_message.reply_document(document=image_url)
        else:
            await m.reply_document(document=image_url)
    except BaseException as e:
        return await m.reply_text(f"Erro!\n{e}")


@Client.on_message(filters.cmd(command="slap", action="Dar um tapa."))
async def slap(c: Client, m: Message):
    r = await http.get(NEKO_URL + "slap")
    if r.status_code == 200:
        image_url = (r.json())["url"]
    else:
        return await m.reply_text(f"Erro!\n**{response.status}**")

    try:
        if m.reply_to_message:
            await m.reply_to_message.reply_document(document=image_url)
        else:
            await m.reply_document(document=image_url)
    except BaseException as e:
        return await m.reply_text(f"Erro!\n{e}")


@Client.on_message(filters.cmd(command="waifu", action="Retorna uma waifu."))
async def waifu(c: Client, m: Message):
    r = await http.get(NEKO_URL + "waifu")
    if r.status_code == 200:
        image_url = (r.json())["url"]
    else:
        return await m.reply_text(f"Erro!\n**{response.status}**")

    try:
        if m.reply_to_message:
            await m.reply_to_message.reply_photo(image_url)
        else:
            await m.reply_photo(image_url)
    except BaseException as e:
        return await m.reply_text(f"Erro!\n{e}")


@Client.on_message(filters.cmd(command="neko", action="Retorna uma Neko."))
async def neko(c: Client, m: Message):
    r = await http.get(NEKO_URL + "neko")
    if r.status_code == 200:
        image_url = (r.json())["url"]
    else:
        return await m.reply_text(f"Erro!\n**{response.status}**")

    try:
        if m.reply_to_message:
            await m.reply_to_message.reply_photo(image_url)
        else:
            await m.reply_photo(image_url)
    except BaseException as e:
        return await m.reply_text(f"Erro!\n{e}")


@Client.on_message(filters.cmd(command="shrug", action="Em caso de dúvida."))
async def shrug(c: Client, m: Message):
    react = random.choice(SHRUGS_REACT)
    if m.reply_to_message:
        await m.reply_to_message.reply_text(react)
    else:
        await m.reply_text(react)


@Client.on_message(filters.cmd(command="react", action="Reações aleatórias."))
async def reacts(c: Client, m: Message):
    react = random.choice(REACTS)
    if m.reply_to_message:
        await m.reply_to_message.reply_text(react)
    else:
        await m.reply_text(react)


@Client.on_message(
    filters.cmd(command="f (?P<text>.+)", action="Press F to Pay Respects.")
)
async def payf(c: Client, m: Message):
    paytext = m.matches[0]["text"]
    pay = "{}\n{}\n{}\n{}\n{}\n{}\n{}\n{}\n{}\n{}\n{}\n{}".format(
        paytext * 8,
        paytext * 8,
        paytext * 2,
        paytext * 2,
        paytext * 2,
        paytext * 6,
        paytext * 6,
        paytext * 2,
        paytext * 2,
        paytext * 2,
        paytext * 2,
        paytext * 2,
    )
    await m.reply_text(pay)

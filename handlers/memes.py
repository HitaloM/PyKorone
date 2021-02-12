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
import base64
import rapidjson as json
from io import BytesIO
from PIL import Image

from pyrogram import Client, filters
from pyrogram.types import Message

from utils import http
from handlers.utils.random import SHRUGS_REACT, REACTS
from handlers.utils.thonkify_dict import thonkifydict

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


@Client.on_message(
    filters.cmd(command="thonkify (?P<text>.+)", action="Entenda o que é na prática.")
)
async def thonkify(c: Client, m: Message):
    if not m.reply_to_message:
        msg = m.text.split(None, 1)[1]
    else:
        msg = m.reply_to_message.text

    if (len(msg)) > 39:
        await m.reply_text("Pense você mesmo...")
        return

    tracking = Image.open(
        BytesIO(
            base64.b64decode(
                "iVBORw0KGgoAAAANSUhEUgAAAAYAAAOACAYAAAAZzQIQAAAALElEQVR4nO3BAQ0AAADCoPdPbQ8HFAAAAAAAAAAAAAAAAAAAAAAAAAAAAPwZV4AAAfA8WFIAAAAASUVORK5CYII="
            )
        )
    )

    for character in msg:
        if character not in thonkifydict:
            msg = msg.replace(character, "")

    x = 0
    y = 896
    image = Image.new("RGBA", [x, y], (0, 0, 0))
    for character in msg:
        value = thonkifydict.get(character)
        addedimg = Image.new(
            "RGBA", [x + value.size[0] + tracking.size[0], y], (0, 0, 0)
        )
        addedimg.paste(image, [0, 0])
        addedimg.paste(tracking, [x, 0])
        addedimg.paste(value, [x + tracking.size[0], 0])
        image = addedimg
        x = x + value.size[0] + tracking.size[0]

    maxsize = 1024, 896
    if image.size[0] > maxsize[0]:
        image.thumbnail(maxsize, Image.ANTIALIAS)

    with BytesIO() as buffer:
        buffer.name = "image.webp"
        image.save(buffer, "PNG")
        buffer.seek(0)
        await m.reply_sticker(buffer)

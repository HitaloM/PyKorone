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

import base64
import html
import random
import re
from io import BytesIO

from PIL import Image
from pyrogram import Client, filters
from pyrogram.errors import BadRequest
from pyrogram.types import Message

from korone.handlers import COMMANDS_HELP
from korone.handlers.utils.random import PASTAMOJIS, REACTS, SHRUGS_REACT
from korone.handlers.utils.thonkify_dict import thonkifydict
from korone.utils import http

GROUP = "memes"

COMMANDS_HELP[GROUP] = {
    "name": "Memes",
    "text": "Esse é meu módulo de memes, divirta-se.",
    "commands": {},
    "help": True,
}


async def neko_api(c: Client, m: Message, text: str = None):
    NEKO_URL = "https://nekos.life/api/v2/img/"
    r = await http.get(NEKO_URL + text)
    if r.status_code == 200:
        image_url = (r.json())["url"]
    else:
        await m.reply_text(f"<b>Erro!</b>\n<code>{r.status}</code>")
        return

    try:
        if m.reply_to_message:
            if text in ("neko", "waifu"):
                await m.reply_to_message.reply_photo(image_url)
            else:
                await m.reply_to_message.reply_document(image_url)
        elif not m.reply_to_message:
            if text in ("neko", "waifu"):
                await m.reply_photo(image_url)
            else:
                await m.reply_document(image_url)
    except BaseException as e:
        await m.reply_text(f"<b>Erro!</b>\n<code>{e}</code>")
        return


@Client.on_message(filters.cmd(command="hug", action="Dar um abraço.", group=GROUP))
async def hug(c: Client, m: Message):
    await neko_api(c, m, "hug")


@Client.on_message(
    filters.cmd(command="pat", action="Dar uma batida na cabeça.", group=GROUP)
)
async def pat(c: Client, m: Message):
    await neko_api(c, m, "pat")


@Client.on_message(filters.cmd(command="slap", action="Dar um tapa.", group=GROUP))
async def slap(c: Client, m: Message):
    await neko_api(c, m, "slap")


@Client.on_message(
    filters.cmd(command="waifu", action="Retorna uma waifu.", group=GROUP)
)
async def waifu(c: Client, m: Message):
    await neko_api(c, m, "waifu")


@Client.on_message(filters.cmd(command="neko", action="Retorna uma Neko.", group=GROUP))
async def neko(c: Client, m: Message):
    await neko_api(c, m, "neko")


@Client.on_message(
    filters.cmd(
        command="vapor(\s(?P<text>.+))?",
        action="Vaporize algo.",
        group=GROUP,
    )
)
async def vapor(c: Client, m: Message):
    text = m.matches[0]["text"]
    if not text:
        if m.reply_to_message:
            text = m.reply_to_message.text
        else:
            await m.reply_text("Eu preciso de texto...")
            return

    reply = []
    for charac in text:
        if 0x21 <= ord(charac) <= 0x7F:
            reply.append(chr(ord(charac) + 0xFEE0))
        elif ord(charac) == 0x20:
            reply.append(chr(0x3000))
        else:
            reply.append(charac)

    vaporized_text = "".join(reply)

    try:
        if m.reply_to_message:
            await m.reply_to_message.reply_text(f"{html.escape(reply)}")
        else:
            await m.reply_text(f"{html.escape(reply)}")
    except BadRequest:
        return


@Client.on_message(
    filters.cmd(
        command="uwu(\s(?P<text>.+))?",
        action="Nokofique um texto.",
        group=GROUP,
    )
)
async def nekofy(c: Client, m: Message):
    args = m.matches[0]["text"]
    if not args:
        if m.reply_to_message:
            args = m.reply_to_message.text
        else:
            await m.reply_text("Eu não posso nokoficar o void.")
            return

    reply = re.sub(r"(r|l)", "w", args)
    reply = re.sub(r"(R|L)", "W", reply)
    reply = re.sub(r"n([aeiou])", r"ny\1", reply)
    reply = re.sub(r"N([aeiouAEIOU])", r"Ny\1", reply)
    reply = reply.replace("ove", "uv")

    try:
        if m.reply_to_message:
            await m.reply_to_message.reply_text(f"{html.escape(reply)}")
        else:
            await m.reply_text(f"{html.escape(reply)}")
    except BadRequest:
        return


@Client.on_message(
    filters.cmd(
        command="cp(\s(?P<text>.+))?",
        action="Torne algo em um copypasta.",
        group=GROUP,
    )
)
async def copypasta(c: Client, m: Message):
    text = m.matches[0]["text"]
    if not text:
        if m.reply_to_message:
            text = m.reply_to_message.text
        else:
            await m.reply_text("Eu preciso de texto...")
            return

    reply = random.choice(PASTAMOJIS)
    try:
        b_char = random.choice(text).lower()
    except BaseException:
        return
    for owo in text:
        if owo == " ":
            reply += random.choice(PASTAMOJIS)
        elif owo in PASTAMOJIS:
            reply += owo
            reply += random.choice(PASTAMOJIS)
        elif owo.lower() == b_char:
            reply += "🅱️"
        else:
            reply += owo.upper() if bool(random.getrandbits(1)) else owo.lower()
    reply += random.choice(PASTAMOJIS)

    try:
        if m.reply_to_message:
            await m.reply_to_message.reply_text(f"{html.escape(reply)}")
        else:
            await m.reply_text(f"{html.escape(reply)}")
    except BadRequest:
        return


@Client.on_message(
    filters.cmd(
        command="mock(\s(?P<text>.+))?",
        action="Mock um texto.",
        group=GROUP,
    )
)
async def mock(c: Client, m: Message):
    text = m.matches[0]["text"]
    if not text:
        if m.reply_to_message:
            text = m.reply_to_message.text
        else:
            await m.reply_text("Eu preciso de texto...")
            return

    reply = []
    for charac in text:
        if charac.isalpha() and random.randint(0, 1):
            to_app = charac.upper() if charac.islower() else charac.lower()
            reply.append(to_app)
        else:
            reply.append(charac)
    mocked_text = "".join(reply)

    try:
        if m.reply_to_message:
            await m.reply_to_message.reply_text(f"{html.escape(mocked_text)}")
        else:
            await m.reply_text(f"{html.escape(mocked_text)}")
    except BadRequest:
        return


@Client.on_message(
    filters.cmd(
        command="clap(\s(?P<text>.+))?",
        action="Palmas.",
        group=GROUP,
    )
)
async def clap(c: Client, m: Message):
    text = m.matches[0]["text"]
    if not text:
        if m.reply_to_message:
            text = m.reply_to_message.text
        else:
            await m.reply_text("Eu preciso de texto...")
            return

    clapped_text = re.sub(" ", " 👏 ", text)
    reply = f"👏 {clapped_text} 👏"

    try:
        if m.reply_to_message:
            await m.reply_to_message.reply_text(f"{html.escape(reply)}")
        else:
            await m.reply_text(f"{html.escape(reply)}")
    except BadRequest:
        return


@Client.on_message(
    filters.cmd(
        command="stretch(\s(?P<text>.+))?",
        action="Estique um texto.",
        group=GROUP,
    )
)
async def stretch(c: Client, m: Message):
    text = m.matches[0]["text"]
    if not text:
        if m.reply_to_message:
            text = m.reply_to_message.text
        else:
            await m.reply_text("Eu preciso de texto...")
            return

    reply = re.sub(
        r"([aeiouAEIOUａｅｉｏｕＡＥＩＯＵаеиоуюяыэё])", (r"\1" * random.randint(3, 10)), text
    )

    try:
        if m.reply_to_message:
            await m.reply_to_message.reply_text(f"{html.escape(reply)}")
        else:
            await m.reply_text(f"{html.escape(reply)}")
    except BadRequest:
        return


@Client.on_message(
    filters.cmd(command="shrug", action="Em caso de dúvida.", group=GROUP)
)
async def shrug(c: Client, m: Message):
    react = random.choice(SHRUGS_REACT)
    if m.reply_to_message:
        await m.reply_to_message.reply_text(react)
    else:
        await m.reply_text(react)


@Client.on_message(
    filters.cmd(command="react", action="Reações aleatórias.", group=GROUP)
)
async def reacts(c: Client, m: Message):
    react = random.choice(REACTS)
    if m.reply_to_message:
        await m.reply_to_message.reply_text(react)
    else:
        await m.reply_text(react)


@Client.on_message(
    filters.cmd(
        command="thonkify (?P<text>.+)",
        action="Entenda o que é na prática.",
        group=GROUP,
    )
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

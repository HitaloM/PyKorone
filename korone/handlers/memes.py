# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2022 Amano Team

import html
import random

from pyrogram import filters
from pyrogram.errors import BadRequest
from pyrogram.types import Message

from korone.bot import Korone
from korone.handlers import COMMANDS_HELP
from korone.handlers.utils.random import PASTAMOJIS, REACTS, SHRUGS_REACT
from korone.utils import http

GROUP = "memes"

COMMANDS_HELP[GROUP] = {
    "name": "Memes",
    "text": "Esse é meu módulo de memes, divirta-se.",
    "commands": {},
    "help": True,
}


async def neko_api(c: Korone, m: Message, text: str = None):
    NEKO_URL = "https://nekos.life/api/v2/img/"
    r = await http.get(NEKO_URL + text)
    if r.status_code == 200:
        image_url = (r.json())["url"]
    else:
        await m.reply_text(f"<b>Erro!</b>\n<code>{r.status}</code>")
        return

    try:
        if m.reply_to_message:
            if text in {"neko", "waifu"}:
                await m.reply_to_message.reply_photo(image_url)
            else:
                await m.reply_to_message.reply_document(image_url)
        elif text in {"neko", "waifu"}:
            await m.reply_photo(image_url)
        else:
            await m.reply_document(image_url)
    except BadRequest as e:
        await m.reply_text(f"<b>Erro!</b>\n<code>{e}</code>")
        return


@Korone.on_message(filters.cmd(command="hug", action="Dar um abraço.", group=GROUP))
async def hug(c: Korone, m: Message):
    await neko_api(c, m, "hug")


@Korone.on_message(
    filters.cmd(command="pat", action="Dar uma batida na cabeça.", group=GROUP)
)
async def pat(c: Korone, m: Message):
    await neko_api(c, m, "pat")


@Korone.on_message(filters.cmd(command="slap", action="Dar um tapa.", group=GROUP))
async def slap(c: Korone, m: Message):
    await neko_api(c, m, "slap")


@Korone.on_message(
    filters.cmd(command="waifu", action="Retorna uma waifu.", group=GROUP)
)
async def waifu(c: Korone, m: Message):
    await neko_api(c, m, "waifu")


@Korone.on_message(filters.cmd(command="neko", action="Retorna uma Neko.", group=GROUP))
async def neko(c: Korone, m: Message):
    await neko_api(c, m, "neko")


@Korone.on_message(
    filters.cmd(
        command=r"vapor(\s(?P<text>.+))?",
        action="Vaporize algo.",
        group=GROUP,
    )
)
async def vapor(c: Korone, m: Message):
    text = m.matches[0]["text"]
    if not text and m.reply_to_message:
        if (m.reply_to_message.text or m.reply_to_message.caption) is not None:
            text = m.reply_to_message.text or m.reply_to_message.caption
        else:
            await m.reply_text("Eu preciso de texto...")
            return

    if not text and not m.reply_to_message:
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
            await m.reply_to_message.reply_text(f"{html.escape(vaporized_text)}")
        else:
            await m.reply_text(f"{html.escape(vaporized_text)}")
    except BadRequest:
        return


@Korone.on_message(
    filters.cmd(
        command=r"cp(\s(?P<text>.+))?",
        action="Torne algo em um copypasta.",
        group=GROUP,
    )
)
async def copypasta(c: Korone, m: Message):
    text = m.matches[0]["text"]
    if not text and m.reply_to_message:
        if (m.reply_to_message.text or m.reply_to_message.caption) is not None:
            text = m.reply_to_message.text or m.reply_to_message.caption
        else:
            await m.reply_text("Eu preciso de texto...")
            return

    if not text and not m.reply_to_message:
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


@Korone.on_message(
    filters.cmd(command="shrug", action="Em caso de dúvida.", group=GROUP)
)
async def shrug(c: Korone, m: Message):
    react = random.choice(SHRUGS_REACT)
    if m.reply_to_message:
        await m.reply_to_message.reply_text(react)
    else:
        await m.reply_text(react)


@Korone.on_message(
    filters.cmd(command="react", action="Reações aleatórias.", group=GROUP)
)
async def reacts(c: Korone, m: Message):
    react = random.choice(REACTS)
    if m.reply_to_message:
        await m.reply_to_message.reply_text(react)
    else:
        await m.reply_text(react)

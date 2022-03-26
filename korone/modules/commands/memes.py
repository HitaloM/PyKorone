# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2022 Amano Team
#
# This file is part of Korone (Telegram Bot)

import html
import random
import re

from pyrogram import filters
from pyrogram.errors import BadRequest
from pyrogram.types import Message

from korone.korone import Korone
from korone.modules import COMMANDS_HELP
from korone.utils import http
from korone.utils.args import get_args_str
from korone.utils.random import PASTAMOJIS, REACTS, SHRUGS_REACT

GROUP = "memes"

COMMANDS_HELP[GROUP] = {
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


@Korone.on_message(filters.cmd(command=r"hug", action=r"Dar um abraço.", group=GROUP))
async def hug(c: Korone, m: Message):
    await neko_api(c, m, "hug")


@Korone.on_message(
    filters.cmd(command=r"pat", action=r"Dar uma batida na cabeça.", group=GROUP)
)
async def pat(c: Korone, m: Message):
    await neko_api(c, m, "pat")


@Korone.on_message(filters.cmd(command=r"slap", action=r"Dar um tapa.", group=GROUP))
async def slap(c: Korone, m: Message):
    await neko_api(c, m, "slap")


@Korone.on_message(
    filters.cmd(command=r"waifu", action=r"Retorna uma waifu.", group=GROUP)
)
async def waifu(c: Korone, m: Message):
    await neko_api(c, m, "waifu")


@Korone.on_message(
    filters.cmd(command=r"neko", action=r"Retorna uma Neko.", group=GROUP)
)
async def neko(c: Korone, m: Message):
    await neko_api(c, m, "neko")


@Korone.on_message(
    filters.cmd(
        command=r"vapor",
        action=r"Vaporize algo.",
        group=GROUP,
    )
)
async def vapor(c: Korone, m: Message):
    text = get_args_str(m)
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
        command=r"uwu",
        action=r"Nokofique um texto.",
        group=GROUP,
    )
)
async def nekofy(c: Korone, m: Message):
    args = get_args_str(m)
    if not args and m.reply_to_message:
        if (m.reply_to_message.text or m.reply_to_message.caption) is not None:
            args = m.reply_to_message.text or m.reply_to_message.caption
        else:
            await m.reply_text("Eu não posso nokoficar o void.")
            return

    if not args and not m.reply_to_message:
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


@Korone.on_message(
    filters.cmd(
        command=r"cp",
        action=r"Torne algo em um copypasta.",
        group=GROUP,
    )
)
async def copypasta(c: Korone, m: Message):
    text = get_args_str(m)
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
    filters.cmd(
        command=r"mock",
        action=r"Mock um texto.",
        group=GROUP,
    )
)
async def mock(c: Korone, m: Message):
    text = get_args_str(m)
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


@Korone.on_message(
    filters.cmd(
        command=r"clap",
        action=r"Palmas.",
        group=GROUP,
    )
)
async def clap(c: Korone, m: Message):
    text = get_args_str(m)
    if not text and m.reply_to_message:
        if (m.reply_to_message.text or m.reply_to_message.caption) is not None:
            text = m.reply_to_message.text or m.reply_to_message.caption
        else:
            await m.reply_text("Eu preciso de texto...")
            return

    if not text and not m.reply_to_message:
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


@Korone.on_message(
    filters.cmd(
        command=r"stretch",
        action=r"Estique um texto.",
        group=GROUP,
    )
)
async def stretch(c: Korone, m: Message):
    text = get_args_str(m)
    if not text and m.reply_to_message:
        if (m.reply_to_message.text or m.reply_to_message.caption) is not None:
            text = m.reply_to_message.text or m.reply_to_message.caption
        else:
            await m.reply_text("Eu preciso de texto...")
            return

    if not text and not m.reply_to_message:
        await m.reply_text("Eu preciso de texto...")
        return

    reply = re.sub(
        r"([aeiouAEIOUａｅｉｏｕＡＥＩＯＵаеиоуюяыэё])",
        (r"\1" * random.randint(3, 10)),
        text,
    )

    try:
        if m.reply_to_message:
            await m.reply_to_message.reply_text(f"{html.escape(reply)}")
        else:
            await m.reply_text(f"{html.escape(reply)}")
    except BadRequest:
        return


@Korone.on_message(
    filters.cmd(command=r"shrug", action=r"Em caso de dúvida.", group=GROUP)
)
async def shrug(c: Korone, m: Message):
    react = random.choice(SHRUGS_REACT)
    if m.reply_to_message:
        await m.reply_to_message.reply_text(react)
    else:
        await m.reply_text(react)


@Korone.on_message(
    filters.cmd(command=r"react", action=r"Reações aleatórias.", group=GROUP)
)
async def reacts(c: Korone, m: Message):
    react = random.choice(REACTS)
    if m.reply_to_message:
        await m.reply_to_message.reply_text(react)
    else:
        await m.reply_text(react)

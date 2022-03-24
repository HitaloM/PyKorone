# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2022 Amano Team
#
# This file is part of Korone (Telegram Bot)

import html
import random
import re

from pyrogram import filters
from pyrogram.types import Message

from korone.korone import Korone
from korone.modules import COMMANDS_HELP
from korone.utils.random import (
    AYY_REACT,
    BANHAMMERS,
    DOGE_REACT,
    FUCK_REACT,
    GODZILLA_REACT,
    IMBACK_REACT,
    REACTS,
    UWU_REACT,
)

GROUP = "messages"

COMMANDS_HELP[GROUP] = {
    "name": "Mensagens",
    "text": "Envie qualquer um desses filtros em algum grupo em que eu estou ou no meu PV.",
    "filters": {},
    "help": True,
}


@Korone.on_message(
    filters.int(filter=r"(sexo+|sex+|sexy)", translate=False, group=GROUP)
)
async def sexo(c: Korone, m: Message):
    await c.send_sticker(
        chat_id=m.chat.id,
        reply_to_message_id=m.message_id,
        sticker="CAACAgEAAx0ET2XwHwACXhRgDhGeDumnwAvIoNsqdCXZHEmk0gACdwIAAjFpvDZsvaEGCsVJsB4E",
    )


@Korone.on_message(filters.int(filter="imback", group=GROUP))
async def voltei(c: Korone, m: Message):
    react = random.choice(IMBACK_REACT)
    await m.reply_text((react).format(m.from_user.first_name))


@Korone.on_message(filters.int(filter=r"triggered", translate=False, group=GROUP))
async def triggered(c: Korone, m: Message):
    await m.reply_animation(
        animation="CgACAgQAAx0ET2XwHwABAQ9NYKkOyHC7bLdTOy3IpeUBmffTvq4AAkgHAAIexRBTnlSg75ETFeceBA",
    )


@Korone.on_message(filters.int(filter=r"rip", translate=False, group=GROUP))
async def rip(c: Korone, m: Message):
    await m.reply_text("❀◟(ó ̯ ò, )")


@Korone.on_message(filters.int(filter=r"f", translate=False, group=GROUP))
async def press_f(c: Korone, m: Message):
    await m.reply_text("F")


@Korone.on_message(filters.int(filter="morning", group=GROUP))
async def good_morning(c: Korone, m: Message):
    react = random.choice(REACTS)
    await m.reply_text("Bom dia! " + react)


@Korone.on_message(filters.int(filter="night", group=GROUP))
async def good_night(c: Korone, m: Message):
    react = random.choice(REACTS)
    await m.reply_text("Boa noite! " + react)


@Korone.on_message(filters.int(filter=r"python", translate=False, group=GROUP))
async def python(c: Korone, m: Message):
    await m.reply_text("is a snake 🐍")


@Korone.on_message(filters.int(filter=r"sleepy|brb|/afk", translate=False, group=GROUP))
async def sleepy(c: Korone, m: Message):
    await m.reply_text(". . . (∪｡∪)｡｡｡zzzZZ")


@Korone.on_message(filters.int(filter=r"baka", translate=False, group=GROUP))
async def baka(c: Korone, m: Message):
    await m.reply_text("Baaaka >3<")


@Korone.on_message(filters.int(filter=r"(@|)VegaData", translate=False, group=GROUP))
async def vegano(c: Korone, m: Message):
    await m.reply_voice(
        voice="AwACAgEAAx0ETZVb2AABEOhnYAhMJjsPaTvD6v0nDcU29uAhU0oAAhcBAAJ58kBELrkMROt69u0eBA",
        caption="Eae parças, beeeleza?! ^-^",
    )


@Korone.on_message(filters.int(filter=r"grr+", translate=False, group=GROUP))
async def grr(c: Korone, m: Message):
    await m.reply_text("😡")


@Korone.on_message(filters.int(filter=r"bruh", translate=False, group=GROUP))
async def bruh(c: Korone, m: Message):
    await m.reply_text("moment")


@Korone.on_message(filters.int(filter="fuck", group=GROUP))
async def fuck(c: Korone, m: Message):
    react = random.choice(FUCK_REACT)
    await m.reply_text(react)


@Korone.on_message(filters.int(filter=r"(doge|doggo)", translate=False, group=GROUP))
async def doge(c: Korone, m: Message):
    react = random.choice(DOGE_REACT)
    await m.reply_text(react)


@Korone.on_message(filters.int(filter=r"ayy", translate=False, group=GROUP))
async def ayy(c: Korone, m: Message):
    react = random.choice(AYY_REACT)
    await m.reply_text(react)


@Korone.on_message(filters.int(filter=r"uwu", translate=False, group=GROUP))
async def uwu(c: Korone, m: Message):
    react = random.choice(UWU_REACT)
    await m.reply_text(react)


@Korone.on_message(filters.int(filter=r"banhammer", translate=False, group=GROUP))
async def banhammer(c: Korone, m: Message):
    react = random.choice(BANHAMMERS)
    await m.reply_sticker(react)


@Korone.on_message(filters.int(filter=r"/(ban|kick)me", translate=False, group=GROUP))
async def kickme(c: Korone, m: Message):
    await m.reply_text("Idiota... UwU")


@Korone.on_message(filters.int(filter=r"ban", translate=False, group=GROUP))
async def ban_dice(c: Korone, m: Message):
    react = (
        "CAACAgEAAx0CT2XwHwACWb5f8IhBw1kQL4BZ5C-W2xQUb8TmLQACqwADMWm8NnADxrv2ioYwHgQ"
    )
    await m.reply_sticker(react)


@Korone.on_message(
    filters.int(filter=r"(#TeamKong|GCam|GCam Brasil)", translate=False, group=GROUP)
)
async def dont_speak_macaco(c: Korone, m: Message):
    react = (
        "CAACAgEAAx0ET2XwHwACZ7RgEaeKJJiQThi77Lnqkk0z4EdvkAACeQIAAjFpvDZT3XS9JPmVyh4E"
    )
    await m.reply_sticker(react)


@Korone.on_message(
    filters.int(filter=r"(Macaco|monkey|King Kong|Kong)", translate=False, group=GROUP)
)
async def macaco(c: Korone, m: Message):
    react = (
        "CAACAgEAAx0CT2XwHwACZ85gEao3lyREsYvlC45rdIs2_BashQACfAIAAjFpvDY9CqNjin13aR4E"
    )
    await m.reply_sticker(react)


@Korone.on_message(
    filters.int(filter=r"rt", translate=False, group=GROUP)
    & filters.reply
    & filters.group
)
async def rtcommand(c: Korone, m: Message):
    reply = m.reply_to_message
    user = m.from_user

    rt_text = None
    rt_text = reply.caption if reply.media else reply.text
    if rt_text is None:
        return

    if reply.from_user.first_name is None:
        return

    if not re.match("🔃 .* retweetou:\n\n👤 .*", rt_text):
        text = f"🔃 <b>{html.escape(user.first_name)}</b> retweetou:\n\n"
        text += f"👤 <b>{html.escape(reply.from_user.first_name)}</b>:"
        text += f" <i>{html.escape(rt_text)}</i>"

        await reply.reply_text(
            text,
            disable_web_page_preview=True,
            disable_notification=True,
        )


@Korone.on_message(
    filters.int(filter=r"Sopa de (macaco|mamaco)", translate=False, group=GROUP)
)
async def sopa_de_macaco(c: Korone, m: Message):
    react = random.choice(GODZILLA_REACT)
    await m.reply_sticker(react)


@Korone.on_message(filters.int(filter=r"hamster", translate=False, group=GROUP))
async def hamster(c: Korone, m: Message):
    await c.send_sticker(
        chat_id=m.chat.id,
        reply_to_message_id=m.message_id,
        sticker="CAACAgEAAxkDAAJHomCNz3Z_wkvAXJDK1t6regj-Z7TzAAKGAQACksphRNFqROtXZ1hmHgQ",
    )


@Korone.on_message(filters.int(filter=r"marimbondo", translate=False, group=GROUP))
async def marimbondo(c: Korone, m: Message):
    await c.send_sticker(
        chat_id=m.chat.id,
        reply_to_message_id=m.message_id,
        sticker="CAACAgEAAxkBAAJX12CP-xtHmZYkAAGVEZWyD3BNynJ2LQACWAEAAtZ0eESGMNhu53i1Yh4E",
    )


@Korone.on_message(filters.int(filter="imsad", group=GROUP))
async def im_sad(c: Korone, m: Message):
    await m.reply_text(
        f"Ah não {html.escape(m.from_user.first_name)}, por que você está triste...?\n"
        "Talvez Korone possa fazer algo por você? ^^"
    )

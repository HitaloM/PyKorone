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

import html
import random
import re

from pyrogram import Client, filters
from pyrogram.types import Message

from korone.handlers import COMMANDS_HELP
from korone.handlers.utils.random import (
    AYY_REACT,
    BANHAMMERS,
    DOGE_REACT,
    FUCK_REACT,
    GODZILLA_REACT,
    IMBACK_REACT,
    REACTS,
    THONKI,
    UWU_REACT,
)

GROUP = "messages"

COMMANDS_HELP[GROUP] = {
    "name": "Mensagens",
    "text": "Envie qualquer um desses filtros em algum grupo em que eu estou ou no meu PV.",
    "filters": {},
    "help": True,
}


@Client.on_message(filters.int(filter=r"koto", group=GROUP))
async def koto(c: Client, m: Message):
    await c.send_sticker(
        chat_id=m.chat.id,
        reply_to_message_id=m.message_id,
        sticker="CAACAgQAAx0CT2XwHwACWD5f78orS_P4vhpvK29jDz2LE4Ju4QAC2QEAAgYlKAOlyAtKtsFCAAEeBA",
    )


@Client.on_message(filters.int(filter=r"(sexo+|sex)", group=GROUP))
async def sexo(c: Client, m: Message):
    await c.send_sticker(
        chat_id=m.chat.id,
        reply_to_message_id=m.message_id,
        sticker="CAACAgEAAx0ET2XwHwACXhRgDhGeDumnwAvIoNsqdCXZHEmk0gACdwIAAjFpvDZsvaEGCsVJsB4E",
    )


@Client.on_message(filters.int(filter=r"(pensando|thonki)", group=GROUP))
async def thonki(c: Client, m: Message):
    react = random.choice(THONKI)
    await m.reply_sticker(react)


@Client.on_message(filters.int(filter=r"yee", group=GROUP))
async def yee(c: Client, m: Message):
    await m.reply_text("o(≧∇≦)o")


@Client.on_message(filters.int(filter=r"(t(o|ô) de volta|voltei)", group=GROUP))
async def voltei(c: Client, m: Message):
    react = random.choice(IMBACK_REACT)
    await m.reply_text((react).format(m.from_user.first_name))


@Client.on_message(filters.int(filter=r"(tuturu|tutturu)", group=GROUP))
async def tutturu(c: Client, m: Message):
    await m.reply_voice(
        voice="AwACAgEAAxkDAAICbF_zg6fjeuwvbffAkVFdO2_YHw9ZAALmAAOSG5hHmkWo5sdCqkUeBA",
        quote=True,
    )


@Client.on_message(filters.int(filter=r"triggered", group=GROUP))
async def triggered(c: Client, m: Message):
    await m.reply_voice(
        voice="CgACAgQAAx0ET2XwHwACXX9gCE6VI4wLfStiWuwXeIoNi3t22AACSAcAAh7FEFOeVKDvkRMV5x4E",
        quote=True,
    )


@Client.on_message(filters.int(filter=r"(\$php|\<?php)", group=GROUP))
async def php(c: Client, m: Message):
    await m.reply_text("Isso é P-PHP? TwT\n*se esconde*")


@Client.on_message(filters.int(filter=r"rip", group=GROUP))
async def rip(c: Client, m: Message):
    await m.reply_text("❀◟(ó ̯ ò, )")


@Client.on_message(filters.int(filter=r"f", group=GROUP))
async def press_f(c: Client, m: Message):
    await m.reply_text("F")


@Client.on_message(filters.int(filter=r"bom dia", group=GROUP))
async def good_morning(c: Client, m: Message):
    react = random.choice(REACTS)
    await m.reply_text("Bom dia! " + react)


@Client.on_message(filters.int(filter=r"boa noite", group=GROUP))
async def good_night(c: Client, m: Message):
    react = random.choice(REACTS)
    await m.reply_text("Boa noite! " + react)


@Client.on_message(filters.int(filter=r"python", group=GROUP))
async def python(c: Client, m: Message):
    await m.reply_text("is a snake 🐍")


@Client.on_message(filters.int(filter=r"(sleepy|brb)", group=GROUP))
async def sleepy(c: Client, m: Message):
    await m.reply_text(". . . (∪｡∪)｡｡｡zzzZZ")


@Client.on_message(filters.int(filter=r"baka", group=GROUP))
async def baka(c: Client, m: Message):
    await m.reply_text("Baaaka >3<")


@Client.on_message(filters.int(filter=r"(@|)VegaData", group=GROUP))
async def vegano(c: Client, m: Message):
    await m.reply_voice(
        voice="AwACAgEAAx0ETZVb2AABEOhnYAhMJjsPaTvD6v0nDcU29uAhU0oAAhcBAAJ58kBELrkMROt69u0eBA",
        caption="Eae parças, beeeleza?! ^-^",
        quote=True,
    )


@Client.on_message(filters.int(filter=r"isso n(ã|a)o funciona", group=GROUP))
async def not_working(c: Client, m: Message):
    await m.reply_text("Apenas formate isso.")


@Client.on_message(filters.int(filter=r"grr+", group=GROUP))
async def grr(c: Client, m: Message):
    await m.reply_text("😡")


@Client.on_message(filters.int(filter=r"bruh", group=GROUP))
async def bruh(c: Client, m: Message):
    await m.reply_text("moment")


@Client.on_message(filters.int(filter=r"porra", group=GROUP))
async def fuck(c: Client, m: Message):
    react = random.choice(FUCK_REACT)
    await m.reply_text(react)


@Client.on_message(filters.int(filter=r"(doge|doggo)", group=GROUP))
async def doge(c: Client, m: Message):
    react = random.choice(DOGE_REACT)
    await m.reply_text(react)


@Client.on_message(filters.int(filter=r"ayy", group=GROUP))
async def ayy(c: Client, m: Message):
    react = random.choice(AYY_REACT)
    await m.reply_text(react)


@Client.on_message(filters.int(filter=r"uwu", group=GROUP))
async def uwu(c: Client, m: Message):
    react = random.choice(UWU_REACT)
    await m.reply_text(react)


@Client.on_message(filters.int(filter=r"banhammer", group=GROUP))
async def banhammer(c: Client, m: Message):
    react = random.choice(BANHAMMERS)
    await m.reply_sticker(react)


@Client.on_message(filters.int(filter=r"/(ban|kick)me", group=GROUP))
async def kickme(c: Client, m: Message):
    await m.reply_text("Idiota... UwU")


@Client.on_message(filters.int(filter=r"ban", group=GROUP))
async def ban_dice(c: Client, m: Message):
    react = (
        "CAACAgEAAx0CT2XwHwACWb5f8IhBw1kQL4BZ5C-W2xQUb8TmLQACqwADMWm8NnADxrv2ioYwHgQ"
    )
    await m.reply_sticker(react)


@Client.on_message(filters.int(filter=r"(#TeamKong|GCam|GCam Brasil)", group=GROUP))
async def dont_speak_macaco(c: Client, m: Message):
    react = (
        "CAACAgEAAx0ET2XwHwACZ7RgEaeKJJiQThi77Lnqkk0z4EdvkAACeQIAAjFpvDZT3XS9JPmVyh4E"
    )
    await m.reply_sticker(react)


@Client.on_message(filters.int(filter=r"(Macaco|King Kong|Kong)", group=GROUP))
async def macaco(c: Client, m: Message):
    react = (
        "CAACAgEAAx0CT2XwHwACZ85gEao3lyREsYvlC45rdIs2_BashQACfAIAAjFpvDY9CqNjin13aR4E"
    )
    await m.reply_sticker(react)


@Client.on_message(
    filters.int(filter=r"rt", group=GROUP) & filters.reply & filters.group
)
async def rtcommand(c: Client, m: Message):
    rt_text = None
    if m.reply_to_message.media:
        rt_text = m.reply_to_message.caption
    else:
        rt_text = m.reply_to_message.text

    if rt_text is None:
        return

    if not re.match("🔃 .* retweetou:\n\n👤 .*", rt_text):
        text = f"🔃 <b>{html.escape(m.from_user.first_name)}</b> retweetou:\n\n"
        text += f"👤 <b>{html.escape(m.reply_to_message.from_user.first_name)}</b>:"
        text += f" <i>{html.escape(rt_text)}</i>"

        await m.reply_to_message.reply_text(text, disable_web_page_preview=True)


@Client.on_message(filters.int(filter=r"Sopa de (Macaco|Mamaco)", group=GROUP))
async def sopa_de_macaco(c: Client, m: Message):
    react = random.choice(GODZILLA_REACT)
    await m.reply_sticker(react)


@Client.on_message(filters.int(filter=r"hamster", group=GROUP))
async def hamster(c: Client, m: Message):
    await c.send_sticker(
        chat_id=m.chat.id,
        reply_to_message_id=m.message_id,
        sticker="CAACAgEAAxkDAAJHomCNz3Z_wkvAXJDK1t6regj-Z7TzAAKGAQACksphRNFqROtXZ1hmHgQ",
    )


@Client.on_message(filters.int(filter=r"marimbondo", group=GROUP))
async def marimbondo(c: Client, m: Message):
    await c.send_sticker(
        chat_id=m.chat.id,
        reply_to_message_id=m.message_id,
        sticker="CAACAgEAAxkBAAJX12CP-xtHmZYkAAGVEZWyD3BNynJ2LQACWAEAAtZ0eESGMNhu53i1Yh4E",
    )

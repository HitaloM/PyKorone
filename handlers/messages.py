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
from datetime import datetime

from pyrogram import Client, filters
from pyrogram.types import Message

from handlers.utils.random import (
    AYY_REACT,
    BANHAMMERS,
    DOGE_REACT,
    FUCK_REACT,
    UWU_REACT,
    IMBACK_REACT,
    GODZILLA_REACT,
)


@Client.on_message(filters.regex(r"(?i)^koto(\.)?$"))
async def koto(c: Client, m: Message):
    await c.send_sticker(
        chat_id=m.chat.id,
        reply_to_message_id=m.message_id,
        sticker="CAACAgQAAx0CT2XwHwACWD5f78orS_P4vhpvK29jDz2LE4Ju4QAC2QEAAgYlKAOlyAtKtsFCAAEeBA",
    )


@Client.on_message(filters.regex(r"(?i)^(sexo|sex)(\.)?$"))
async def sexo(c: Client, m: Message):
    await c.send_sticker(
        chat_id=m.chat.id,
        reply_to_message_id=m.message_id,
        sticker="CAACAgEAAx0ET2XwHwACXhRgDhGeDumnwAvIoNsqdCXZHEmk0gACdwIAAjFpvDZsvaEGCsVJsB4E",
    )


@Client.on_message(filters.regex(r"(?i)^yee(\.)?$"))
async def yee(c: Client, m: Message):
    await m.reply_text("o(≧∇≦)o")


@Client.on_message(filters.regex(r"(?i)^(t(o|ô) de volta|voltei)(\.)?$"))
async def voltei(c: Client, m: Message):
    react = random.choice(IMBACK_REACT)
    await m.reply_text((react).format(m.from_user.first_name))


@Client.on_message(filters.regex(r"(?i)^(tuturu|tutturu)(\.)?$"))
async def tutturu(c: Client, m: Message):
    await m.reply_voice(
        voice="AwACAgEAAxkDAAICbF_zg6fjeuwvbffAkVFdO2_YHw9ZAALmAAOSG5hHmkWo5sdCqkUeBA",
        quote=True,
    )


@Client.on_message(filters.regex(r"(?i)^triggered(\.)?$"))
async def triggered(c: Client, m: Message):
    await m.reply_voice(
        voice="CgACAgQAAx0ET2XwHwACXX9gCE6VI4wLfStiWuwXeIoNi3t22AACSAcAAh7FEFOeVKDvkRMV5x4E",
        quote=True,
    )


@Client.on_message(filters.regex(r"(?i)(\$php|\<?php)"))
async def php(c: Client, m: Message):
    await m.reply_text("Isso é P-PHP? TwT\n*se esconde*")


@Client.on_message(filters.regex(r"(?i)^rip(\.)?$"))
async def rip(c: Client, m: Message):
    await m.reply_text("❀◟(ó ̯ ò, )")


@Client.on_message(filters.regex(r"(?i)^f(\.)?$"))
async def press_f(c: Client, m: Message):
    await m.reply_text("F")


@Client.on_message(filters.regex(r"(?i)^python(\.)?$"))
async def python(c: Client, m: Message):
    await m.reply_text("is a snake 🐍")


@Client.on_message(filters.regex(r"(?i)^(sleepy|brb)(\.)?$"))
async def sleepy(c: Client, m: Message):
    await m.reply_text(". . . (∪｡∪)｡｡｡zzzZZ")


@Client.on_message(filters.regex(r"(?i)^baka(\.)?$"))
async def baka(c: Client, m: Message):
    await m.reply_text("Baaaka >3<")


@Client.on_message(filters.regex(r"(?i)^(@|)VegaData(\.)?$"))
async def vegano(c: Client, m: Message):
    await m.reply_voice(
        voice="AwACAgEAAx0ETZVb2AABEOhnYAhMJjsPaTvD6v0nDcU29uAhU0oAAhcBAAJ58kBELrkMROt69u0eBA",
        caption="Eae parças, beeeleza?! ^-^",
        quote=True
    )


@Client.on_message(filters.regex(r"(?i)^isso n(ã|a)o funciona(\.)?$"))
async def not_working(c: Client, m: Message):
    await m.reply_text("Apenas formate isso.")


@Client.on_message(filters.regex(r"(?i)^grr+(\.)?$"))
async def grr(c: Client, m: Message):
    await m.reply_text("😡")


@Client.on_message(filters.regex(r"(?i)^bruh(\.)?$"))
async def bruh(c: Client, m: Message):
    await m.reply_text("moment")


@Client.on_message(filters.regex(r"(?i)^(yeet|ainda)(\.)?$"))
async def yeet(c: Client, m: Message):
    first = datetime.now()
    yeet = await m.reply_text("<b>Preparando...</b>")
    second = datetime.now()
    time = (second - first).microseconds / 1000
    await yeet.edit_text(f"*joga um cookie à <code>{time} m/s</code>*\nAINDA")


@Client.on_message(filters.regex(r"(?i)^porra(\.)?$"))
async def fuck(c: Client, m: Message):
    react = random.choice(FUCK_REACT)
    await m.reply_text(react)


@Client.on_message(filters.regex(r"(?i)^doge|doggo(\.)?$"))
async def doge(c: Client, m: Message):
    react = random.choice(DOGE_REACT)
    await m.reply_text(react)


@Client.on_message(filters.regex(r"(?i)^ayy(\.)?$"))
async def ayy(c: Client, m: Message):
    react = random.choice(AYY_REACT)
    await m.reply_text(react)


@Client.on_message(filters.regex(r"(?i)^uwu(\.)?$"))
async def uwu(c: Client, m: Message):
    react = random.choice(UWU_REACT)
    await m.reply_text(react)


@Client.on_message(filters.regex(r"(?i)^banhammer(\.)?$"))
async def banhammer(c: Client, m: Message):
    react = random.choice(BANHAMMERS)
    await c.send_sticker(
        chat_id=m.chat.id, reply_to_message_id=m.message_id, sticker=react
    )


@Client.on_message(filters.regex(r"(?i)^ban(\.)?$"))
async def ban_dice(c: Client, m: Message):
    react = (
        "CAACAgEAAx0CT2XwHwACWb5f8IhBw1kQL4BZ5C-W2xQUb8TmLQACqwADMWm8NnADxrv2ioYwHgQ"
    )
    await c.send_sticker(
        chat_id=m.chat.id, reply_to_message_id=m.message_id, sticker=react
    )


@Client.on_message(filters.regex(r"(?i)^(#TeamKong|GCam|GCam Brasil)(\.)?$"))
async def dont_speak_macaco(c: Client, m: Message):
    react = (
        "CAACAgEAAx0ET2XwHwACZ7RgEaeKJJiQThi77Lnqkk0z4EdvkAACeQIAAjFpvDZT3XS9JPmVyh4E"
    )
    await c.send_sticker(
        chat_id=m.chat.id, reply_to_message_id=m.message_id, sticker=react
    )


@Client.on_message(filters.regex(r"(?i)^(Macaco|King Kong|Kong)(\.)?$"))
async def macaco(c: Client, m: Message):
    react = (
        "CAACAgEAAx0CT2XwHwACZ85gEao3lyREsYvlC45rdIs2_BashQACfAIAAjFpvDY9CqNjin13aR4E"
    )
    await c.send_sticker(
        chat_id=m.chat.id, reply_to_message_id=m.message_id, sticker=react
    )


@Client.on_message(filters.regex(r"(?i)^Sopa de (Macaco|Mamaco)(\.)?$"))
async def sopa_de_macaco(c: Client, m: Message):
    react = random.choice(GODZILLA_REACT)
    await c.send_sticker(
        chat_id=m.chat.id, reply_to_message_id=m.message_id, sticker=react
    )

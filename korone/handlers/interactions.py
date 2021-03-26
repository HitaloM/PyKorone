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

import random

from pyrogram import Client, filters
from pyrogram.types import Message

from korone.handlers.utils.random import (
    HEY_REACT,
    INSULTS_REACT,
    RANDOM_REACT,
    WHATSUP_REACT,
)
from korone.handlers import COMMANDS_HELP

GROUP = "interactions"

COMMANDS_HELP[GROUP] = {
    "name": "Interações",
    "text": "Use estes filtros em resposta a mim.",
    "filters": {},
    "help": True,
}


@Client.on_message(
    filters.int(filter=r"(Quem te criou|Quem criou voc(ê|e))", group=GROUP)
)
async def my_creator(c: Client, m: Message):
    text = "Meu criador se chama Hitalo ^^"

    if m.chat.type == "private":
        await m.reply_text(text)
    elif (
        m.reply_to_message and m.reply_to_message.from_user.id == (await c.get_me()).id
    ):
        await m.reply_text(text)
        return


@Client.on_message(filters.int(filter=r"(okay|ok)", group=GROUP))
async def okay(c: Client, m: Message):
    text = "Hmm..."

    if m.chat.type == "private":
        await m.reply_text(text)
    elif (
        m.reply_to_message and m.reply_to_message.from_user.id == (await c.get_me()).id
    ):
        await m.reply_text(text)
        return


@Client.on_message(filters.int(filter=r"voc(e|ê) gosta de caf(é|e)", group=GROUP))
async def ulikecoffe(c: Client, m: Message):
    text = "Com certeza! ☕"

    if m.chat.type == "private":
        await m.reply_text(text)
    elif (
        m.reply_to_message and m.reply_to_message.from_user.id == (await c.get_me()).id
    ):
        await m.reply_text(text)
        return


@Client.on_message(
    filters.int(filter=r"Korone, voc(e|ê) gosta de caf(é|e)", group=GROUP)
)
async def ulikecoffe_list(c: Client, m: Message):
    try:
        answer = await m.chat.ask(
            "Com certeza! Gostaria de uma xícara de café?",
            filters=filters.user(m.from_user.id),
            timeout=60,
        )

        if answer.text.lower().startswith(("nao", "não")):
            await answer.reply_text("Tudo bem! :D")
        elif answer.text.lower().startswith("sim"):
            await answer.reply_text("Que bom! Aqui está ☕ ^^")
        else:
            await answer.reply_text("Compreendo! U~U")

    except BaseException:
        await m.reply_text("Fui ignorado... qwq")
        return


@Client.on_message(filters.int(filter=r"(Ol(á|a)|Oi|Eae|Hi|Hello|Hey)", group=GROUP))
async def hello(c: Client, m: Message):
    react = random.choice(HEY_REACT)

    if m.chat.type == "private":
        await m.reply_text((react).format(m.from_user.first_name))
    elif (
        m.reply_to_message and m.reply_to_message.from_user.id == (await c.get_me()).id
    ):
        await m.reply_text((react).format(m.from_user.first_name))
        return


@Client.on_message(
    filters.int(
        filter=r"(Est(ú|u)pido|Puta|Vai se f(o|u)der|Idiota|Ot(á|a)rio|Lixo)",
        group=GROUP,
    )
)
async def insult(c: Client, m: Message):
    react = random.choice(INSULTS_REACT)

    if m.chat.type == "private":
        await m.reply_text((react).format(m.from_user.first_name))
    elif (
        m.reply_to_message and m.reply_to_message.from_user.id == (await c.get_me()).id
    ):
        await m.reply_text((react).format(m.from_user.first_name))
        return


@Client.on_message(filters.int(filter=r"(como vai|tudo bem)", group=GROUP))
async def all_right(c: Client, m: Message):
    react = random.choice(WHATSUP_REACT)

    if m.chat.type == "private":
        await m.reply_text(react)
    elif (
        m.reply_to_message and m.reply_to_message.from_user.id == (await c.get_me()).id
    ):
        await m.reply_text(react)
        return


@Client.on_message(filters.int(filter=r"Korone, tudo bem", group=GROUP))
async def all_right_list(c: Client, m: Message):
    try:
        answer = await m.chat.ask(
            "Estou bem! Você está bem?",
            filters=filters.user(m.from_user.id),
            timeout=60,
        )

        if answer.text.lower().startswith(("nao", "não")):
            await answer.reply_text("Que pena. T-T")
        elif answer.text.lower().startswith("sim"):
            await answer.reply_text("Que bom! ^^")
        else:
            await answer.reply_text("Compreendo! U~U")

    except BaseException:
        await m.reply_text("Fui ignorado... qwq")
        return


@Client.on_message(~filters.private)
async def random_react(c: Client, m: Message):
    if m.message_id % 100 != 0:
        m.continue_propagation()
    react = random.choice(RANDOM_REACT)
    if isinstance(react, tuple):
        react = random.choice(react)

    await m.reply_text(react, quote=False)
    m.continue_propagation()

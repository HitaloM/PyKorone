# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2022 Amano Team

import html
import random

from pyrogram import filters
from pyrogram.types import Message

from korone.bot import Korone
from korone.handlers import COMMANDS_HELP
from korone.handlers.utils.random import (
    HEY_REACT,
    INSULTS_REACT,
    SHUTUP_REACT,
    WHATSUP_REACT,
)

GROUP = "interactions"

COMMANDS_HELP[GROUP] = {
    "name": "Interações",
    "text": "Use estes filtros em resposta a mim.",
    "filters": {},
    "help": True,
}


@Korone.on_message(filters.int(filter=r"obrigado", group=GROUP))
async def thank_you(c: Korone, m: Message):
    await c.int_reply(m, f"De nada, {html.escape(m.from_user.first_name)}! ^^")


@Korone.on_message(
    filters.int(filter=r"(Quem te criou|Quem criou voc(ê|e))", group=GROUP)
)
async def my_creator(c: Korone, m: Message):
    await c.int_reply(m, "Meu criador se chama Hitalo ^^")


@Korone.on_message(filters.int(filter=r"(okay|ok)", group=GROUP))
async def okay(c: Korone, m: Message):
    await c.int_reply(m, "Hmm...")


@Korone.on_message(filters.int(filter=r"voc(e|ê) gosta de caf(é|e)", group=GROUP))
async def ulikecoffe(c: Korone, m: Message):
    await c.int_reply(m, "Com certeza! ☕")


@Korone.on_message(filters.int(filter=r"(Ol(á|a)|Oi|Eae|Hi|Hello|Hey)", group=GROUP))
async def hello(c: Korone, m: Message):
    react = random.choice(HEY_REACT)
    if m.from_user is not None:
        await c.int_reply(m, react.format(m.from_user.first_name))


@Korone.on_message(
    filters.int(
        filter=r"(Est(ú|u)pido|Puta|Vai se f(o|u)der|Idiota|Ot(á|a)rio|Lixo)",
        group=GROUP,
    )
)
async def insult(c: Korone, m: Message):
    if m.from_user is not None:
        react = random.choice(INSULTS_REACT)
        await c.int_reply(m, react.format(m.from_user.first_name))


@Korone.on_message(filters.int(filter=r"(como vai|tudo bem)", group=GROUP))
async def all_right(c: Korone, m: Message):
    if m.from_user is not None:
        react = random.choice(WHATSUP_REACT)
        await c.int_reply(m, react)


@Korone.on_message(filters.int(filter=r"(Cala boca|Cala-boca|calaboca)", group=GROUP))
async def shutup(c: Korone, m: Message):
    if m.from_user is not None:
        react = random.choice(SHUTUP_REACT)
        await c.int_reply(m, react)

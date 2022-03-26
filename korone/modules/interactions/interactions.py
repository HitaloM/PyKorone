# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2022 Amano Team
#
# This file is part of Korone (Telegram Bot)

import html
import random

from pyrogram import filters
from pyrogram.types import Message

from korone.korone import Korone
from korone.modules import COMMANDS_HELP
from korone.utils import leave_if_muted
from korone.utils.random import (
    HEY_REACT,
    INSULTS_REACT,
    RANDOM_REACT,
    SHUTUP_REACT,
    WHATSUP_REACT,
)

GROUP = "interactions"

COMMANDS_HELP[GROUP] = {
    "text": "Use estes filtros em resposta a mim.",
    "filters": {},
    "help": True,
}


@Korone.on_message(filters.int(filter="thanks", group=GROUP))
async def thank_you(c: Korone, m: Message):
    await c.int_reply(m, f"De nada, {html.escape(m.from_user.first_name)}! ^^")


@Korone.on_message(filters.int(filter="creator", group=GROUP))
async def my_creator(c: Korone, m: Message):
    await c.int_reply(m, "Meu criador se chama Hitalo ^^")


@Korone.on_message(filters.int(filter="okay", group=GROUP))
async def okay(c: Korone, m: Message):
    await c.int_reply(m, "Hmm...")


@Korone.on_message(filters.int(filter="ulikecoffe", group=GROUP))
async def ulikecoffe(c: Korone, m: Message):
    await c.int_reply(m, "Com certeza! ☕")


@Korone.on_message(filters.int(filter="hello", group=GROUP))
async def hello(c: Korone, m: Message):
    react = random.choice(HEY_REACT)
    if m.from_user is not None:
        await c.int_reply(m, react.format(m.from_user.first_name))


@Korone.on_message(
    filters.int(
        filter="insult",
        group=GROUP,
    )
)
async def insult(c: Korone, m: Message):
    if m.from_user is not None:
        react = random.choice(INSULTS_REACT)
        await c.int_reply(m, react.format(m.from_user.first_name))


@Korone.on_message(filters.int(filter="howru", group=GROUP))
async def all_right(c: Korone, m: Message):
    if m.from_user is not None:
        react = random.choice(WHATSUP_REACT)
        await c.int_reply(m, react)


@Korone.on_message(filters.int(filter="shutup", group=GROUP))
async def shutup(c: Korone, m: Message):
    if m.from_user is not None:
        react = random.choice(SHUTUP_REACT)
        await c.int_reply(m, react)


@Korone.on_message(~filters.private & ~filters.edited)
@leave_if_muted
async def random_react(c: Korone, m: Message):
    if m.message_id % 100 != 0:
        m.continue_propagation()
    react = random.choice(RANDOM_REACT)
    if isinstance(react, tuple):
        react = random.choice(react)

    await c.send_message(m.chat.id, react)
    m.continue_propagation()

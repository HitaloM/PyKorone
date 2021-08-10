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

from pyrogram import filters
from pyrogram.types import Message

from korone.handlers import COMMANDS_HELP
from korone.handlers.utils.random import (
    HEY_REACT,
    INSULTS_REACT,
    RANDOM_REACT,
    SHUTUP_REACT,
    WHATSUP_REACT,
)
from korone.korone import Korone

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
    await c.int_reply(m, react.format(m.from_user.first_name))


@Korone.on_message(
    filters.int(
        filter=r"(Est(ú|u)pido|Puta|Vai se f(o|u)der|Idiota|Ot(á|a)rio|Lixo)",
        group=GROUP,
    )
)
async def insult(c: Korone, m: Message):
    react = random.choice(INSULTS_REACT)
    await c.int_reply(m, react.format(m.from_user.first_name))


@Korone.on_message(filters.int(filter=r"(como vai|tudo bem)", group=GROUP))
async def all_right(c: Korone, m: Message):
    react = random.choice(WHATSUP_REACT)
    await c.int_reply(m, react)


@Korone.on_message(filters.int(filter=r"(Cala boca|Cala-boca|calaboca)", group=GROUP))
async def shutup(c: Korone, m: Message):
    react = random.choice(SHUTUP_REACT)
    await c.int_reply(m, react)


@Korone.on_message(~filters.private & ~filters.edited)
async def random_react(c: Korone, m: Message):
    if m.message_id % 100 != 0:
        m.continue_propagation()
    react = random.choice(RANDOM_REACT)
    if isinstance(react, tuple):
        react = random.choice(react)

    await c.send_message(m.chat.id, react)
    m.continue_propagation()

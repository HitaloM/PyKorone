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

from pyrogram import Client, filters
from pyrogram.types import Message

from handlers.utils.random import WHATSUP_REACT


@Client.on_message(filters.regex(r"(?i)^Oi$"))
async def hi(c: Client, m: Message):
    if m.chat.type == "private":
        await m.reply_text("Olá ^^")
    elif m.reply_to_message and m.reply_to_message.from_user.id == (await c.get_me()).id:
        await m.reply_to_message.reply("Olá ^^")
        return


@Client.on_message(filters.regex(r"(?i)^Ol(á|a)$"))
async def hello(c: Client, m: Message):
    if m.chat.type == "private":
        await m.reply_text("Oi ^^")
    elif m.reply_to_message and m.reply_to_message.from_user.id == (await c.get_me()).id:
        await m.reply_to_message.reply("Oi ^^")
        return


@Client.on_message(filters.regex(r"(?i)^(okay|ok)$"))
async def okay(c: Client, m: Message):
    if m.chat.type == "private":
        await m.reply_text("Hmm...")
    elif m.reply_to_message and m.reply_to_message.from_user.id == (await c.get_me()).id:
        await m.reply_to_message.reply("Hmm...")
        return


@Client.on_message(filters.regex(r"(?i)^Tudo bem(\?|)$"))
async def all_right(c: Client, m: Message):
    react = random.choice(WHATSUP_REACT)
    if m.chat.type == "private":
        await m.reply_text(react)
    elif m.reply_to_message and m.reply_to_message.from_user.id == (await c.get_me()).id:
        await m.reply_to_message.reply(react)
        return

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

import pyrogram
from pyrogram import Client, filters
from pyrogram.types import Message

from handlers.utils.random import (
    WHATSUP_REACT,
    HEY_REACT,
    INSULTS_REACT
)


@Client.on_message(filters.regex(r"(?i)^(Quem te criou|Quem criou voc(ê|))(\?|)$"))
async def my_creator(c: Client, m: Message):
    text = "Meu criador é o @Hitalo ^^"

    if m.chat.type == "private":
        await m.reply_text(text)
    elif m.reply_to_message and m.reply_to_message.from_user.id == (await c.get_me()).id:
        await m.reply_text(text)
        return


@Client.on_message(filters.regex(r"(?i)^(okay|ok)$"))
async def okay(c: Client, m: Message):
    text = "Hmm..."

    if m.chat.type == "private":
        await m.reply_text(text)
    elif m.reply_to_message and m.reply_to_message.from_user.id == (await c.get_me()).id:
        await m.reply_text(text)
        return


@Client.on_message(filters.regex(r"(?i)^(Ol(á|a)|Oi|Eae)$"))
async def hello(c: Client, m: Message):
    react = random.choice(HEY_REACT)

    if m.chat.type == "private":
        await m.reply_text((react).format(m.from_user.first_name))
    elif m.reply_to_message and m.reply_to_message.from_user.id == (await c.get_me()).id:
        await m.reply_text((react).format(m.from_user.first_name))
        return


@Client.on_message(filters.regex(r"(?i)^(Est(ú|u)pido|Puta|Vai se foder|Idiota)$"))
async def insult(c: Client, m: Message):
    react = random.choice(INSULTS_REACT)

    if m.chat.type == "private":
        await m.reply_text((react).format(m.from_user.first_name))
    elif m.reply_to_message and m.reply_to_message.from_user.id == (await c.get_me()).id:
        await m.reply_text((react).format(m.from_user.first_name))
        return


@Client.on_message(filters.regex(r"(?i)^Como vai(\?|)$"))
async def all_right(c: Client, m: Message):
    react = random.choice(WHATSUP_REACT)

    if m.chat.type == "private":
        await m.reply_text(react)
    elif m.reply_to_message and m.reply_to_message.from_user.id == (await c.get_me()).id:
        await m.reply_text(react)
        return


@Client.on_message(filters.regex(r"(?i)^Tudo bem Korone\?$"))
async def all_right(c: Client, m: Message):
    try:
       answer = await m.chat.ask("Estou bem! Você está bem?", filters=filters.user(m.from_user.id), timeout=60)
       if answer.text.lower().startswith("n"):
           await answer.reply("Que pena. T-T", quote=True)
       elif answer.text.lower().startswith("s"):
           await answer.reply("Que bom! ^^", quote=True)
       else:
           await answer.reply("Compreendo! U~U", quote=True)
    except BaseException as err:
       print(err)
       await m.reply("Fui ignorado... qwq", quote=True)
       return

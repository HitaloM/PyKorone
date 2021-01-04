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

import re
import random
import wikipedia

from pyrogram import Client, filters
from pyrogram.types import Message
from pyromod.helpers import ikb

from handlers.utils.httpx import http
from handlers.utils.random import (
    NONE_CMD,
    HELLO,
    REACTIONS,
    CATCH_REACT
)


@Client.on_message(filters.regex(r"(?i)^Korone, gire um dado$"))
async def dice(c: Client, m: Message):
    dicen = await c.send_dice(m.chat.id, reply_to_message_id=m.message_id)
    await dicen.reply_text(
        f"O dado parou no número {dicen.dice.value}")


@Client.on_message(filters.regex(r"(?i)^Korone, remova ele$") & filters.group)
async def kick(c: Client, m: Message):
    await c.kick_chat_member(m.chat.id, m.reply_to_message.from_user.id)
    await m.chat.unban_member(m.reply_to_message.from_user.id)
    await m.reply_animation(
        animation="https://media1.giphy.com/media/MZqLlWvzkkMCc/giphy.gif",
        quote=True)


@Client.on_message(filters.regex(r"(?i)^Korone, me d(ê|e) um cookie$"))
async def give_me_cookie(c: Client, m: Message):
    await m.reply_text(("*dá um cookie à {}* ^^")
                       .format(m.from_user.first_name))


@Client.on_message(filters.regex(r"(?i)^Korone, d(ê|e) um cookie$")
                   & filters.reply)
async def give_cookie(c: Client, m: Message):
    await m.reply_text(("*dá um cookie à {}* ^^")
                       .format(m.reply_to_message.from_user.first_name))


@Client.on_message(filters.regex(r"(?i)^Korone, qual o nome dele$")
                   & filters.reply)
async def tell_name(c: Client, m: Message):
    await m.reply_text(("O nome dele é {}! ^^")
                       .format(m.reply_to_message.from_user.first_name))


@Client.on_message(filters.regex(r"(?i)^Korone, pegue ele$") & filters.reply)
async def catch_him(c: Client, m: Message):
    react = random.choice(CATCH_REACT)
    reaction = random.choice(REACTIONS)
    await m.reply_text((react + reaction)
                       .format(m.reply_to_message.from_user.first_name))


@Client.on_message(filters.regex(r"(?i)^Korone, (me |)conte uma piada$"))
async def dadjoke(c: Client, m: Message):
    response = await http.get("https://icanhazdadjoke.com/", headers={"Accept": "application/json"})
    if response.status_code == 200:
        dad_joke = (response.json())["joke"]
    else:
        await m.reply_text(f"An error occurred: **{response.status_code}**")
        return

    await m.reply_text(dad_joke)


@Client.on_message(filters.regex(r"(?i)^Korone$"))
async def hello(c: Client, m: Message):
    react = random.choice(HELLO)
    await m.reply_text((react).format(m.from_user.first_name))


@Client.on_message(filters.regex(r"(?i)^Korone, o que é (?P<text>.+)"))
async def wiki(c: Client, m: Message):
    args = m.matches[0]['text']
    wikipedia.set_lang("pt")
    try:
        pagewiki = wikipedia.page(args)
    except wikipedia.exceptions.PageError as e:
        await m.reply_text(f"Nenhum resultado encontrado!\nError: <code>{e}</code>")
        return
    except wikipedia.exceptions.DisambiguationError as refer:
        refer = str(refer).split("\n")
        if len(refer) >= 6:
            batas = 6
        else:
            batas = len(refer)
        text = ""
        for x in range(batas):
            if x == 0:
                text += refer[x]+"\n"
            else:
                text += "- `"+refer[x]+"`\n"
        await m.reply_text(text)
        return
    except IndexError:
        return
    title = pagewiki.title
    summary = pagewiki.summary[0:500]
    keyboard = ikb([
        [('🔧 Ler mais...', wikipedia.page(args).url, 'url')]])
    await m.reply_text(("<b>{}</b>\n{}...").format(title, summary), reply_markup=keyboard)

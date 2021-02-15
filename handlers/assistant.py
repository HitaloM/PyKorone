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

import io
import random

import rapidjson as json
import wikipedia
from pyrogram import Client, filters
from pyrogram.types import Message
from pyromod.helpers import ikb
from pyrogram.errors.exceptions.bad_request_400 import BadRequest

from utils import http, translator
from handlers.utils.random import CATCH_REACT, HELLO, REACTIONS
from . import COMMANDS_HELP

GROUP = "assistant"

COMMANDS_HELP[GROUP] = {
    "name": "Assistências",
    "text": "Meus comandos de assistência, use em grupos ou PV.",
    "filters": {},
    "help": True,
}


@Client.on_message(filters.int(filter=r"Korone, gire um dado", group=GROUP))
async def dice(c: Client, m: Message):
    dicen = await c.send_dice(m.chat.id, reply_to_message_id=m.message_id)
    await dicen.reply_text(f"O dado parou no número {dicen.dice.value}")


@Client.on_message(filters.int(filter=r"Korone, remova ele", group=GROUP) & filters.group)
async def kick(c: Client, m: Message):
    member = await c.get_chat_member(chat_id=m.chat.id, user_id=m.from_user.id)
    if member.status in ["administrator", "creator"]:
        try:
            await c.kick_chat_member(m.chat.id, m.reply_to_message.from_user.id)
            await m.chat.unban_member(m.reply_to_message.from_user.id)
            await m.reply_animation(
                animation="CgACAgQAAx0ET2XwHwACWb1gCDScpSaFyoNgPa2Ag_yiRo61YQACPwIAAryMhFOFxHV09aPBTR4E",
                quote=True,
            )
        except BadRequest:
            await m.reply_text("Eu n-não posso remover um administrador! >-<")


@Client.on_message(filters.int(filter=r"Korone, me d(ê|e) um cookie", group=GROUP))
async def give_me_cookie(c: Client, m: Message):
    await m.reply_text(("*dá um cookie à {}* ^^").format(m.from_user.first_name))


@Client.on_message(filters.int(filter=r"Korone, d(ê|e) um cookie", group=GROUP) & filters.reply)
async def give_cookie(c: Client, m: Message):
    await m.reply_text(
        ("*dá um cookie à {}* ^^").format(m.reply_to_message.from_user.first_name)
    )


@Client.on_message(filters.int(filter=r"Korone, morda( ele)?", group=GROUP) & filters.reply)
async def bite(c: Client, m: Message):
    await m.reply_text(("*morde {}*").format(m.reply_to_message.from_user.first_name))


@Client.on_message(filters.int(filter=r"Korone, me abra(c|ç)e", group=GROUP))
async def hug(c: Client, m: Message):
    await m.reply_text(("*Abraça com força {}* ^^").format(m.from_user.first_name))


@Client.on_message(filters.int(filter=r"Korone, qual o nome dele", group=GROUP))
async def tell_name(c: Client, m: Message):
    await m.reply_text(
        ("O nome dele é {}! ^^").format(m.reply_to_message.from_user.first_name)
    )


@Client.on_message(filters.int(filter=r"Korone, pegue ele", group=GROUP) & filters.reply)
async def catch_him(c: Client, m: Message):
    react = random.choice(CATCH_REACT)
    reaction = random.choice(REACTIONS)
    await m.reply_text(
        (react + reaction).format(m.reply_to_message.from_user.first_name)
    )


@Client.on_message(filters.int(filter=r"Korone, (me )?conte uma piada", group=GROUP))
async def dadjoke(c: Client, m: Message):
    response = await http.get(
        "https://icanhazdadjoke.com/", headers={"Accept": "application/json"}
    )

    if response.status_code == 200:
        dad_joke = (response.json())["joke"]
    else:
        await m.reply_text(f"Erro! <code>{response.status_code}</code>")
        return

    await m.reply_text(dad_joke)


@Client.on_message(filters.int(filter=r"Korone, (me )?conte um fato", group=GROUP))
async def useless_fact(c: Client, m: Message):
    response = await http.get(
        "https://uselessfacts.jsph.pl/random.json", params={"language": "en"}
    )

    if response.status_code == 200:
        fact_text = (response.json())["text"].replace("`", "'")
    else:
        await m.reply_text(f"Erro! <code>{response.status_code}</code>")
        return

    fact_text_pt = translator.translate(fact_text, lang_tgt="pt")

    await m.reply_text(fact_text_pt)


@Client.on_message(filters.int(filter=r"Korone", group=GROUP))
async def hello(c: Client, m: Message):
    react = random.choice(HELLO)
    await m.reply_text((react).format(m.from_user.first_name))


@Client.on_message(filters.int(filter=r"Korone, qual o link (de convite )?do grupo", group=GROUP))
async def invitelink(c: Client, m: Message):
    if m.chat.username is None:
        chat = m.chat.id
    else:
        chat = m.chat.username
    link = await c.export_chat_invite_link(chat)
    await m.reply_text(link)


@Client.on_message(filters.int(filter=r"Korone, o que é (?P<text>.+)", group=GROUP))
async def wiki(c: Client, m: Message):
    args = m.matches[0]["text"]
    wikipedia.set_lang("pt")
    try:
        pagewiki = wikipedia.page(args)
    except wikipedia.exceptions.PageError as e:
        await m.reply_text(
            "Desculpe nenhum resultado foi encontrado!\n\n"
            f"<b>Erro</b>: <code>{e}</code>"
        )
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
                text += refer[x] + "\n"
            else:
                text += "- <code>" + refer[x] + "</code>\n"
        await m.reply_text(text)
        return
    except IndexError:
        return
    title = pagewiki.title
    summary = pagewiki.summary[0:500]
    keyboard = ikb([[("Ler mais...", wikipedia.page(args).url, "url")]])
    await m.reply_text(
        ("<b>{}</b>\n{}...").format(title, summary), reply_markup=keyboard
    )


@Client.on_message(filters.int(filter=r"Korone, fa(ç|c)a um dump", group=GROUP) & filters.reply)
async def json_dump(c: Client, m: Message):
    dump = json.dumps(json.loads(str(m)), indent=4, ensure_ascii=False)

    file = io.BytesIO(dump.encode())
    file.name = f"dump_{m.chat.id}x{m.reply_to_message.from_user.id}.json"
    await m.reply_document(file)

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

import io
import json
import random
from typing import Dict

import wikipedia
from pyrogram import filters
from pyrogram.types import Message

from korone.handlers import COMMANDS_HELP
from korone.handlers.utils.random import CATCH_REACT, HELLO, REACTIONS
from korone.korone import Korone
from korone.utils import http

GROUP = "assistant"

COMMANDS_HELP[GROUP]: Dict = {
    "name": "Assistências",
    "text": "Meus comandos de assistência, use em grupos ou PV.",
    "filters": {},
    "help": True,
}


@Korone.on_message(filters.int(filter=r"Korone, gire um dado", group=GROUP))
async def dice(c: Korone, m: Message):
    dicen = await c.send_dice(m.chat.id, reply_to_message_id=m.message_id)
    await dicen.reply_text(f"O dado parou no número <code>{dicen.dice.value}</code>!")


@Korone.on_message(
    filters.int(filter=r"Korone, remova ele", group=GROUP) & filters.group
)
async def kick(c: Korone, m: Message):
    member = await c.get_chat_member(chat_id=m.chat.id, user_id=m.from_user.id)

    if member.can_restrict_members is False:
        return await m.reply_text(
            "Você não possui a permissão para banir usuários neste grupo!"
        )

    if member.status in ["administrator", "creator"]:
        try:
            await c.kick_chat_member(m.chat.id, m.reply_to_message.from_user.id)
            await m.chat.unban_member(m.reply_to_message.from_user.id)
            await m.reply_animation(
                animation="CgACAgQAAx0ET2XwHwACWb1gCDScpSaFyoNgPa2Ag_yiRo61YQACPwIAAryMhFOFxHV09aPBTR4E",
                quote=True,
            )
        except BaseException as e:
            return await m.reply_text(
                f"Eu n-não consegui remover este usuário! >-<\n<b>Erro:</b> <code>{e}</code>"
            )
    else:
        await m.reply_text("Bakayarou! Você não é um administrador...")


@Korone.on_message(filters.int(filter=r"Korone, me d(ê|e) um cookie", group=GROUP))
async def give_me_cookie(c: Korone, m: Message):
    await m.reply_text(("*dá um cookie à {}* ^^").format(m.from_user.first_name))


@Korone.on_message(
    filters.int(filter=r"Korone, d(ê|e) um cookie", group=GROUP) & filters.reply
)
async def give_cookie(c: Korone, m: Message):
    await m.reply_text(
        ("*dá um cookie à {}* ^^").format(m.reply_to_message.from_user.first_name)
    )


@Korone.on_message(
    filters.int(filter=r"Korone, morda( ele)?", group=GROUP) & filters.reply
)
async def bite(c: Korone, m: Message):
    await m.reply_text(("*morde {}*").format(m.reply_to_message.from_user.first_name))


@Korone.on_message(filters.int(filter=r"Korone, me abra(c|ç)e", group=GROUP))
async def hug(c: Korone, m: Message):
    await m.reply_text(("*Abraça com força {}* ^^").format(m.from_user.first_name))


@Korone.on_message(filters.int(filter=r"Korone, qual o nome dele", group=GROUP))
async def tell_name(c: Korone, m: Message):
    await m.reply_text(
        ("O nome dele é {}! ^^").format(m.reply_to_message.from_user.first_name)
    )


@Korone.on_message(
    filters.int(filter=r"Korone, pegue ele", group=GROUP) & filters.reply
)
async def catch_him(c: Korone, m: Message):
    react = random.choice(CATCH_REACT)
    reaction = random.choice(REACTIONS)
    await m.reply_text(
        (react + reaction).format(m.reply_to_message.from_user.first_name)
    )


@Korone.on_message(filters.int(filter=r"Korone, (me )?conte uma piada", group=GROUP))
async def dadjoke(c: Korone, m: Message):
    r = await http.get(
        "https://icanhazdadjoke.com/", headers={"Accept": "application/json"}
    )

    if r.status_code == 200:
        dad_joke = (r.json())["joke"]
    else:
        await m.reply_text(f"Erro! <code>{r.status_code}</code>")
        return

    await m.reply_text(dad_joke)


@Korone.on_message(filters.int(filter=r"Korone, (me )?conte um fato", group=GROUP))
async def useless_fact(c: Korone, m: Message):
    r = await http.get(
        "https://uselessfacts.jsph.pl/random.json", params={"language": "en"}
    )

    if r.status_code == 200:
        fact_text = (r.json())["text"].replace("`", "'")
    else:
        await m.reply_text(f"Erro! <code>{r.status_code}</code>")
        return

    await m.reply_text(fact_text)


@Korone.on_message(filters.int(filter=r"Korone", group=GROUP))
async def hello(c: Korone, m: Message):
    react = random.choice(HELLO)
    await m.reply_text((react).format(m.from_user.first_name))


@Korone.on_message(
    filters.int(filter=r"Korone, qual o link (de convite )?do grupo", group=GROUP)
)
async def invitelink(c: Korone, m: Message):
    chat = m.chat.id if m.chat.username is None else m.chat.username
    link = await c.export_chat_invite_link(chat)
    await m.reply_text(link)


@Korone.on_message(filters.int(filter=r"Korone, o que é (?P<text>.+)", group=GROUP))
async def wiki_search(c: Korone, m: Message):
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
    keyboard = c.ikb([[("Ler mais...", wikipedia.page(args).url, "url")]])
    await m.reply_text(
        ("<b>{}</b>\n{}...").format(title, summary), reply_markup=keyboard
    )


@Korone.on_message(
    filters.int(filter=r"Korone, fa(ç|c)a um dump", group=GROUP) & filters.reply
)
async def json_dump(c: Korone, m: Message):
    dump = json.dumps(json.loads(str(m)), indent=4, ensure_ascii=False)

    file = io.BytesIO(dump.encode())
    file.name = f"dump_{m.chat.id}x{m.reply_to_message.from_user.id}.json"
    await m.reply_document(file)

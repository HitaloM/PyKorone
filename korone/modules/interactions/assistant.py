# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2022 Amano Team
#
# This file is part of Korone (Telegram Bot)

import io
import json
import random

import wikipedia
from pyrogram import enums, filters
from pyrogram.errors import BadRequest, Forbidden
from pyrogram.types import Message

from korone.korone import Korone
from korone.modules import COMMANDS_HELP
from korone.utils import http
from korone.utils.random import CATCH_REACT, HELLO, REACTIONS

GROUP = "assistant"

COMMANDS_HELP[GROUP] = {
    "description": False,
    "filters": {},
    "help": True,
}


@Korone.on_message(filters.int(filter="dice", group=GROUP))
async def dice(c: Korone, m: Message):
    dicen = await c.send_dice(m.chat.id, reply_to_message_id=m.message_id)
    await dicen.reply_text(f"O dado parou no número <code>{dicen.dice.value}</code>!")


@Korone.on_message(filters.int("kick", group=GROUP))
async def kick(c: Korone, m: Message):
    if m.chat.type == enums.ChatType.PRIVATE:
        await m.reply_text("Este comando é para ser usado em grupos!")
        return

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
                animation="CgACAgQAAx0ET2XwHwACWb1gCDScpSaFyoNgPa2Ag_yiRo61YQACPwIAAryMhFOFxHV09aPBTR4E"
            )
        except (BadRequest, Forbidden) as e:
            return await m.reply_text(
                f"Eu n-não consegui remover este usuário! >-<\n<b>Erro:</b> <code>{e}</code>"
            )
    else:
        await m.reply_text("Bakayarou! Você não é um administrador...")


@Korone.on_message(filters.int("give_me_cookie", group=GROUP))
async def give_me_cookie(c: Korone, m: Message):
    if m.from_user is not None:
        await m.reply_text(f"*dá um cookie à {m.from_user.first_name}* ^^")


@Korone.on_message(filters.int("give_cookie", group=GROUP) & filters.reply)
async def give_cookie(c: Korone, m: Message):
    if m.reply_to_message.from_user is not None:
        await m.reply_text(
            f"*dá um cookie à {m.reply_to_message.from_user.first_name}* ^^"
        )


@Korone.on_message(filters.int("bite", group=GROUP) & filters.reply)
async def bite(c: Korone, m: Message):
    if m.reply_to_message.from_user is not None:
        await m.reply_text(f"*morde {m.reply_to_message.from_user.first_name}*")


@Korone.on_message(filters.int("hug", group=GROUP))
async def hug(c: Korone, m: Message):
    if m.from_user is not None:
        await m.reply_text(f"*Abraça com força {m.from_user.first_name}* ^^")


@Korone.on_message(filters.int("tell_name", group=GROUP))
async def tell_name(c: Korone, m: Message):
    if m.reply_to_message.from_user is not None:
        await m.reply_text(
            f"O nome dele é {m.reply_to_message.from_user.first_name}! ^^"
        )


@Korone.on_message(filters.int("catch_him", group=GROUP) & filters.reply)
async def catch_him(c: Korone, m: Message):
    if m.reply_to_message.from_user is not None:
        react = random.choice(CATCH_REACT)
        reaction = random.choice(REACTIONS)
        await m.reply_text(
            (react + reaction).format(m.reply_to_message.from_user.first_name)
        )


@Korone.on_message(filters.int("dadjoke", group=GROUP))
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


@Korone.on_message(filters.int("useless_fact", group=GROUP))
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


@Korone.on_message(filters.int(r"Korone", translate=False, group=GROUP))
async def hello(c: Korone, m: Message):
    if m.from_user is not None:
        react = random.choice(HELLO)
        await m.reply_text((react).format(m.from_user.first_name))


@Korone.on_message(filters.int("invitelink", group=GROUP))
async def invitelink(c: Korone, m: Message):
    chat = m.chat.id if m.chat.username is None else m.chat.username
    try:
        text = await c.export_chat_invite_link(chat)
    except Forbidden as e:
        text = f"Eu estou impedido de executar este comando! >-<\n<b>Erro:</b> <code>{e}</code>"

    await m.reply_text(text)


@Korone.on_message(filters.int("wiki", group=GROUP))
async def wiki(c: Korone, m: Message):
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
        batas = min(len(refer), 6)
        text = "".join(
            refer[x] + "\n" if x == 0 else "- <code>" + refer[x] + "</code>\n"
            for x in range(batas)
        )

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


@Korone.on_message(filters.int("jsondump", group=GROUP) & filters.reply)
async def json_dump(c: Korone, m: Message):
    dump = json.dumps(json.loads(str(m)), indent=4, ensure_ascii=False)

    file = io.BytesIO(dump.encode())
    file.name = f"dump_{m.chat.id}x{m.reply_to_message.from_user.id}.json"
    await m.reply_document(file)

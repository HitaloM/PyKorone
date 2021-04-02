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
import base64
import string
import random
import binascii
import platform
from datetime import datetime, timezone

import pyromod
import pyrogram
import kantex
from pyrogram import Client, filters
from pyrogram.types import Message
from kantex.html import Bold, KeyValueItem, Section, SubSection, Code

import korone
from korone.utils import pretty_size, http, sw
from korone.config import SUDOERS, OWNER, prefix
from korone.database import Users, XPs, Levels
from korone.handlers.utils.reddit import imagefetcher, titlefetcher, bodyfetcher
from korone.handlers import COMMANDS_HELP

GROUP = "general"

COMMANDS_HELP[GROUP] = {
    "name": "Diversos",
    "text": "Este é meu módulo de comandos sem categoria.",
    "commands": {},
    "help": True,
}


@Client.on_message(
    filters.cmd(command="ping", action="Verifique a velocidade de resposta do korone.")
)
async def ping(c: Client, m: Message):
    first = datetime.now()
    sent = await m.reply_text("<b>Pong!</b>")
    second = datetime.now()
    time = (second - first).microseconds / 1000
    await sent.edit_text(f"<b>Pong!</b> <code>{time}</code>ms")


@Client.on_message(
    filters.cmd(
        command="user(\s(?P<text>.+))?",
        action="Retorna algumas informações do usuário.",
    )
)
async def user_info(c: Client, m: Message):
    args = m.matches[0]["text"]
    now_date = datetime.now().replace(tzinfo=timezone.utc)

    try:
        if args:
            user = await c.get_users(f"{args}")
        elif m.reply_to_message:
            user = m.reply_to_message.from_user
        elif not m.reply_to_message and not args:
            user = m.from_user
    except BaseException as e:
        return await m.reply_text(f"<b>Error!</b>\n<code>{e}</code>")

    user_db = (
        await Users.get_or_create(
            {
                "first_name": user.first_name,
                "last_name": user.last_name or "",
                "username": user.username or "",
                "last_update": now_date,
            },
            id=user.id,
        )
    )[0]
    xp_db = (await XPs.get_or_create({"value": 0}, chat_id=m.chat.id, user_id=user.id))[
        0
    ]
    level_db = (
        await Levels.get_or_create({"value": 1}, chat_id=m.chat.id, user_id=user.id)
    )[0]

    text = "<b>Informações do usuário</b>:"
    text += f"\nID: <code>{user.id}</code>"
    text += f"\nNome: {html.escape(user.first_name)}"

    if user.last_name:
        text += f"\nSobrenome: {html.escape(user.last_name)}"

    if user.username:
        text += f"\nNome de Usuário: @{html.escape(user.username)}"

    text += f"\nLink de Usuário: {user.mention('link', style='html')}"

    text += f"\n\nNível: (<b>Global</b>: <code>{user_db.level}</code>, <b>Grupo</b>: <code>{level_db.value}</code>)"
    text += f"\nXP: (<b>Global</b>: <code>{user_db.xp}</code>, <b>Grupo</b>: <code>{xp_db.value}</code>)"

    try:
        spamwatch = sw.get_ban(int(user.id))
        if spamwatch:
            text += "\n\nEste usuário está banido no @SpamWatch!"
            text += f"\nMotivo: <code>{spamwatch.reason}</code>"
    except BaseException:
        pass

    if user.id == OWNER:
        text += "\n\nEste é meu dono - Eu nunca faria algo contra ele!"
    else:
        if user.id in SUDOERS:
            text += (
                "\n\nEssa pessoa é um dos meus usuários sudo! "
                "Quase tão poderoso quanto meu dono, então cuidado."
            )

    await m.reply_text(text)


@Client.on_message(
    filters.cmd(
        command="copy",
        action="Comando originalmente para testes mas que também é divertido.",
    )
    & filters.reply
)
async def copy(c: Client, m: Message):
    try:
        await c.copy_message(
            chat_id=m.chat.id,
            from_chat_id=m.chat.id,
            message_id=m.reply_to_message.message_id,
        )
    except BaseException:
        return


@Client.on_message(
    filters.cmd(
        command="file",
        action="Obtenha informações avançadas de um arquivo.",
    )
    & filters.reply
)
async def file_debug(c: Client, m: Message):
    doc = m.reply_to_message.document

    if not doc:
        return await m.reply_text("Este comando funciona apenas com arquivos!")

    file_date = datetime.utcfromtimestamp(doc.date).strftime("%Y-%m-%d %H:%M:%S")

    text = f"<b>file_name</b>: <code>{doc.file_name}</code>\n"
    text += f"\n<b>file_id</b>: <code>{doc.file_id}</code>"
    text += f"\n<b>file_unique_id</b>: <code>{doc.file_unique_id}</code>"
    text += f"\n<b>file_size</b>: <code>{pretty_size(doc.file_size)}</code>"
    text += f"\n<b>date</b>: <code>{file_date}</code>"
    text += f"\n<b>mime_type</b>: <code>{doc.mime_type}</code>"

    await m.reply_text(text)


@Client.on_message(
    filters.cmd(command="echo (?P<text>.+)", action="Fale através do korone.")
)
async def echo(c: Client, m: Message):
    text = m.matches[0]["text"]
    chat_id = m.chat.id
    kwargs = {}
    reply = m.reply_to_message
    if reply:
        kwargs["reply_to_message_id"] = reply.message_id
    try:
        await m.delete()
    except BaseException:
        pass
    await c.send_message(chat_id=chat_id, text=text, **kwargs)


@Client.on_message(filters.command("py", prefix))
async def dev(c: Client, m: Message):
    source_url = "git.io/JtmRH"
    doc = Section(
        "PyKorone Bot",
        KeyValueItem(Bold("Source"), source_url),
        KeyValueItem(Bold("Korone version"), korone.__version__),
        KeyValueItem(Bold("Pyrogram version"), pyrogram.__version__),
        KeyValueItem(Bold("Pyromod version"), pyromod.__version__),
        KeyValueItem(Bold("Python version"), platform.python_version()),
        KeyValueItem(Bold("KanTeX version"), kantex.__version__),
        KeyValueItem(Bold("System version"), c.system_version),
    )
    await m.reply_text(doc, disable_web_page_preview=True)


@Client.on_message(filters.cmd(command="cat", action="Imagens aleatórias de gatos."))
async def cat_photo(c: Client, m: Message):
    r = await http.get("https://api.thecatapi.com/v1/images/search")
    cat = r.json
    await m.reply_photo(cat()[0]["url"], caption="Meow!! (^つωฅ^)")


@Client.on_message(
    filters.cmd(command="dog", action="Imagens aleatórias de cachorros.")
)
async def dog_photo(c: Client, m: Message):
    r = await http.get("https://random.dog/woof.json")
    dog = r.json()
    await m.reply_photo(dog["url"], caption="Woof!! U・ᴥ・U")


@Client.on_message(filters.cmd(command="fox", action="Imagens aleatórias de raposas."))
async def fox_photo(c: Client, m: Message):
    r = await http.get("https://some-random-api.ml/img/fox")
    fox = r.json()
    await m.reply_photo(fox["link"], caption="What the fox say?")


@Client.on_message(filters.cmd(command="panda", action="Imagens aleatórias de pandas."))
async def panda_photo(c: Client, m: Message):
    r = await http.get("https://some-random-api.ml/img/panda")
    panda = r.json()
    await m.reply_photo(panda["link"], caption="🐼")


@Client.on_message(
    filters.cmd(command="bird", action="Imagens aleatórias de pássaros.")
)
async def bird_photo(c: Client, m: Message):
    r = await http.get("http://shibe.online/api/birds")
    bird = r.json()
    await m.reply_photo(bird[0], caption="🐦")


@Client.on_message(
    filters.cmd(
        command="red(?P<type>.)?(\s(?P<search>.+))?",
        action="Retorna tópicos do Reddit.",
        group=GROUP,
    )
)
async def redimg(c: Client, m: Message):
    fetch_type = m.matches[0]["type"]
    sub = m.matches[0]["search"]

    if not sub:
        await m.reply_text("<b>Use</b>: <code>/red(i|t|b) (nome do subreddit)</code>")
        return

    if fetch_type == "i":
        await imagefetcher(c, m, sub)
    elif fetch_type == "t":
        await titlefetcher(c, m, sub)
    elif fetch_type == "b":
        await bodyfetcher(c, m, sub)


@Client.on_message(
    filters.cmd(command="b64encode (?P<text>.+)", action="Codifique texto em base64.")
)
async def b64e(c: Client, m: Message):
    text = m.matches[0]["text"]
    b64 = base64.b64encode(text.encode("utf-8")).decode()
    await m.reply_text(f"<code>{b64}</code>")


@Client.on_message(
    filters.cmd(command="b64decode (?P<text>.+)", action="Decodifique códigos base64.")
)
async def b64d(c: Client, m: Message):
    text = m.matches[0]["text"]
    try:
        b64 = base64.b64decode(text).decode("utf-8", "replace")
    except binascii.Error as e:
        return await m.reply_text(f"⚠️ Dados base64 inválidos: {e}")
    await m.reply_text(html.escape(b64))


@Client.on_message(filters.cmd(command="empty", action="Envia uma mensagem vazia."))
async def empty(c: Client, m: Message):
    await m.reply_text("\U000e0020")


@Client.on_message(
    filters.cmd(
        command="gencode",
        action="Gera códigos falsos no estilo da Play Store.",
    )
)
async def gencode(c: Client, m: Message):
    count = 10
    length = 23

    codes = []
    alphabet = string.ascii_uppercase + string.digits
    for _ in range(count):
        code = "".join(random.choice(alphabet) for _ in range(length))
        codes.append(code)

    codes_str = "\n".join(codes)
    await m.reply_text(f"<code>{codes_str}</code>")

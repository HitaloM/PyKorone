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

import html
import platform
from datetime import datetime

import kantex
import pyrogram
import pyromod
from config import prefix
from kantex.html import Bold, KeyValueItem, Section
from pyrogram import Client, filters
from pyrogram.types import Message

from utils import http
from config import SUDOERS, OWNER
from . import COMMANDS_HELP

GROUP = "general"

COMMANDS_HELP[GROUP] = {
    "name": "Diversos",
    "text": "Este é meu módulo de comandos sem categoria.",
    "commands": {},
    "help": True,
}


@Client.on_message(
    filters.cmd(command="ping", action="Verifique a velocidade de resposta do bot.")
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

    try:
        if args:
            user = await c.get_users(f"{args}")
        else:
            user = m.reply_to_message.from_user
    except BaseException as e:
        return await m.reply_text(f"<b>Error!</b>\n<code>{e}</code>")

    text = "<b>Informações do usuário:</b>:"
    text += f"\nID: <code>{user.id}</code>"
    text += f"\nNome: {html.escape(user.first_name)}"

    if user.last_name:
        text += f"\nSobrenome: {html.escape(user.last_name)}"

    if user.username:
        text += f"\nNome de Usuário: @{html.escape(user.username)}"

    text += f"\nLink de Usuário: <a href='tg://user?id={user.id}'>link</a>"

    if user.id == OWNER:
        text += "\n\nEste é meu dono - Eu nunca faria algo contra ele!"
    else:
        if user.id in SUDOERS:
            text += (
                "\nEssa pessoa é um dos meus usuários sudo! "
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
    filters.cmd(command="echo (?P<text>.+)", action="Fale através do bot.")
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
        KeyValueItem(Bold("Pyrogram version"), pyrogram.__version__),
        KeyValueItem(Bold("Pyromod version"), pyromod.__version__),
        KeyValueItem(Bold("Python version"), platform.python_version()),
        KeyValueItem(Bold("KanTeX version"), kantex.__version__),
        KeyValueItem(Bold("System version"), c.system_version),
    )
    await m.reply_text(doc, disable_web_page_preview=True)


@Client.on_message(filters.cmd(command="cat", action="Imagens aleatórias de gatos."))
async def cat(c: Client, m: Message):
    r = await http.get("https://api.thecatapi.com/v1/images/search")
    cats = r.json
    await m.reply_photo(cats()[0]["url"], caption="Meow!! (^つωฅ^)")


@Client.on_message(
    filters.cmd(command="dog", action="Imagens aleatórias de cachorros.")
)
async def dog(c: Client, m: Message):
    r = await http.get("https://random.dog/woof.json")
    dogs = r.json()
    await m.reply_photo(dogs["url"], caption="Woof!! U・ᴥ・U")


@Client.on_message(filters.cmd(command="fox", action="Imagens aleatórias de raposas."))
async def fox(c: Client, m: Message):
    r = await http.get("https://some-random-api.ml/img/fox")
    fox = r.json()
    await m.reply_photo(fox["link"], caption="What the fox say?")


@Client.on_message(filters.cmd(command="panda", action="Imagens aleatórias de pandas."))
async def panda(c: Client, m: Message):
    r = await http.get("https://some-random-api.ml/img/panda")
    panda = r.json()
    await m.reply_photo(panda["link"], caption="🐼")


@Client.on_message(
    filters.cmd(command="bird", action="Imagens aleatórias de pássaros.")
)
async def bird(c: Client, m: Message):
    r = await http.get("http://shibe.online/api/birds")
    bird = r.json()
    await m.reply_photo(bird[0], caption="🐦")

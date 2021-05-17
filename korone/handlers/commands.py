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

import base64
import binascii
import html
import os
import random
import shutil
import string
import tempfile
from datetime import datetime
from typing import Dict

import regex
from pyrogram import filters
from pyrogram.errors import BadRequest
from pyrogram.types import Message

from korone.config import OWNER, SUDOERS, SW_API
from korone.handlers import COMMANDS_HELP
from korone.handlers.utils.reddit import bodyfetcher, imagefetcher, titlefetcher
from korone.korone import Korone
from korone.utils import http

GROUP = "general"

COMMANDS_HELP[GROUP]: Dict = {
    "name": "Diversos",
    "text": "Este é meu módulo de comandos sem categoria.",
    "commands": {},
    "help": True,
}


@Korone.on_message(
    filters.cmd(command="ping", action="Verifique a velocidade de resposta do korone.")
)
async def ping(c: Korone, m: Message):
    first = datetime.now()
    sent = await m.reply_text("<b>Pong!</b>")
    second = datetime.now()
    time = (second - first).microseconds / 1000
    await sent.edit_text(f"<b>Pong!</b> <code>{time}</code>ms")


@Korone.on_message(
    filters.cmd(
        command=r"user(\s(?P<text>.+))?",
        action="Retorna algumas informações do usuário.",
    )
)
async def user_info(c: Korone, m: Message):
    args = m.matches[0]["text"]

    try:
        if args:
            user = await c.get_users(f"{args}")
        elif m.reply_to_message:
            user = m.reply_to_message.from_user
        elif not m.reply_to_message and not args:
            user = m.from_user
    except BaseException as e:
        return await m.reply_text(f"<b>Error!</b>\n<code>{e}</code>")

    text = "<b>Informações do usuário</b>:"
    text += f"\nID: <code>{user.id}</code>"
    text += f"\nNome: {html.escape(user.first_name)}"

    if user.last_name:
        text += f"\nSobrenome: {html.escape(user.last_name)}"

    if user.username:
        text += f"\nNome de Usuário: @{html.escape(user.username)}"

    text += f"\nLink de Usuário: {user.mention('link', style='html')}"

    r = await http.get(
        f"https://api.spamwat.ch/banlist/{int(user.id)}",
        headers={"Authorization": f"Bearer {SW_API}"},
    )
    if r.status_code == 200:
        ban = r.json()
        text += "\n\nEste usuário está banido no @SpamWatch!"
        text += f"\nMotivo: <code>{ban['reason']}</code>"

    if user.id == OWNER:
        text += "\n\nEste é meu dono - Eu nunca faria algo contra ele!"
    elif user.id in SUDOERS:
        text += (
            "\n\nEssa pessoa é um dos meus usuários sudo! "
            "Quase tão poderoso quanto meu dono, então cuidado."
        )

    await m.reply_text(text)


@Korone.on_message(
    filters.cmd(
        command="copy$",
        action="Comando originalmente para testes mas que também é divertido.",
    )
    & filters.reply
)
async def copy(c: Korone, m: Message):
    try:
        await c.copy_message(
            chat_id=m.chat.id,
            from_chat_id=m.chat.id,
            message_id=m.reply_to_message.message_id,
        )
    except BadRequest:
        return


@Korone.on_message(
    filters.cmd(
        command="file$",
        action="Obtenha informações técnicas de uma mídia.",
    )
    & filters.reply
)
async def file_debug(c: Korone, m: Message):
    media = (
        m.reply_to_message.photo
        or m.reply_to_message.sticker
        or m.reply_to_message.animation
        or m.reply_to_message.video
        or m.reply_to_message.document
    )

    if not media:
        await m.reply_text("Nenhuma mídia encontrado!")
        return

    await m.reply_text(
        f"<code>{media}</code>",
        disable_web_page_preview=True,
    )


@Korone.on_message(filters.cmd(command="cat", action="Imagens aleatórias de gatos."))
async def cat_photo(c: Korone, m: Message):
    r = await http.get("https://api.thecatapi.com/v1/images/search")
    if not r.status_code == 200:
        return await m.reply_text(f"<b>Error!</b> <code>{r.status_code}</code>")
    cat = r.json
    await m.reply_photo(cat()[0]["url"], caption="Meow!! (^つωฅ^)")


@Korone.on_message(
    filters.cmd(command="dog", action="Imagens aleatórias de cachorros.")
)
async def dog_photo(c: Korone, m: Message):
    r = await http.get("https://dog.ceo/api/breeds/image/random")
    if not r.status_code == 200:
        return await m.reply_text(f"<b>Error!</b> <code>{r.status_code}</code>")
    dog = r.json()
    await m.reply_photo(dog["message"], caption="Woof!! U・ᴥ・U")


@Korone.on_message(filters.cmd(command="fox", action="Imagens aleatórias de raposas."))
async def fox_photo(c: Korone, m: Message):
    r = await http.get("https://some-random-api.ml/img/fox")
    if not r.status_code == 200:
        return await m.reply_text(f"<b>Error!</b> <code>{r.status_code}</code>")
    fox = r.json()
    await m.reply_photo(fox["link"], caption="What the fox say?")


@Korone.on_message(filters.cmd(command="panda", action="Imagens aleatórias de pandas."))
async def panda_photo(c: Korone, m: Message):
    r = await http.get("https://some-random-api.ml/img/panda")
    if not r.status_code == 200:
        return await m.reply_text(f"<b>Error!</b> <code>{r.status_code}</code>")
    panda = r.json()
    await m.reply_photo(panda["link"], caption="🐼")


@Korone.on_message(
    filters.cmd(command="bird", action="Imagens aleatórias de pássaros.")
)
async def bird_photo(c: Korone, m: Message):
    r = await http.get("http://shibe.online/api/birds")
    if not r.status_code == 200:
        return await m.reply_text(f"<b>Error!</b> <code>{r.status_code}</code>")
    bird = r.json()
    await m.reply_photo(bird[0], caption="🐦")


@Korone.on_message(
    filters.cmd(command="redpanda", action="Imagens aleatórias de pandas vermelhos.")
)
async def rpanda_photo(c: Korone, m: Message):
    r = await http.get("https://some-random-api.ml/img/red_panda")
    if not r.status_code == 200:
        return await m.reply_text(f"<b>Error!</b> <code>{r.status_code}</code>")
    rpanda = r.json()
    await m.reply_photo(rpanda["link"], caption="🐼")


@Korone.on_message(
    filters.cmd(
        command=r"red(?P<type>.)?(\s(?P<search>.+))?",
        action="Retorna tópicos do Reddit.",
        group=GROUP,
    )
)
async def redimg(c: Korone, m: Message):
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


@Korone.on_message(
    filters.cmd(
        command=r"b64encode(\s(?P<text>.+))?", action=r"Codifique texto em base64."
    )
)
async def b64e(c: Korone, m: Message):
    text = m.matches[0]["text"]
    if not text:
        if m.reply_to_message:
            text = m.reply_to_message.text
        else:
            await m.reply_text("Eu preciso de texto...")
            return
    b64 = base64.b64encode(text.encode("utf-8")).decode()
    await m.reply_text(f"<code>{b64}</code>")


@Korone.on_message(
    filters.cmd(
        command=r"b64decode(\s(?P<text>.+))?", action=r"Decodifique códigos base64."
    )
)
async def b64d(c: Korone, m: Message):
    text = m.matches[0]["text"]
    if not text:
        if m.reply_to_message:
            text = m.reply_to_message.text
        else:
            await m.reply_text("Eu preciso de texto...")
            return
    try:
        b64 = base64.b64decode(text).decode("utf-8", "replace")
    except binascii.Error as e:
        return await m.reply_text(f"⚠️ Dados base64 inválidos: <code>{e}</code>")
    await m.reply_text(html.escape(b64))


@Korone.on_message(filters.cmd(command="empty", action="Envia uma mensagem vazia."))
async def empty(c: Korone, m: Message):
    await c.send_message(
        chat_id=m.chat.id,
        reply_to_message_id=m.message_id,
        text="\U000e0020",
    )


@Korone.on_message(
    filters.cmd(
        command="gencode",
        action="Gera códigos falsos no estilo da Play Store.",
    )
)
async def gencode(c: Korone, m: Message):
    count = 10
    length = 23

    codes = []
    alphabet = string.ascii_uppercase + string.digits
    for _ in range(count):
        code = "".join(random.choice(alphabet) for _ in range(length))
        codes.append(code)

    codes_str = "\n".join(codes)
    await m.reply_text(f"<code>{codes_str}</code>")


@Korone.on_message(filters.regex(r"^s/(.+)?/(.+)?(/.+)?") & filters.reply)
async def sed(c: Korone, m: Message):
    exp = regex.split(r"(?<![^\\]\\)/", m.text)
    pattern = exp[1]
    replace_with = exp[2].replace(r"\/", "/")
    flags = exp[3] if len(exp) > 3 else ""

    count = 1
    rflags = 0

    if "g" in flags:
        count = 0
    if "i" in flags and "s" in flags:
        rflags = regex.I | regex.S
    elif "i" in flags:
        rflags = regex.I
    elif "s" in flags:
        rflags = regex.S

    text = m.reply_to_message.text or m.reply_to_message.caption

    if not text:
        return

    try:
        res = regex.sub(
            pattern, replace_with, text, count=count, flags=rflags, timeout=1
        )
    except TimeoutError:
        await m.reply_text("Ops, seu padrão regex durou muito tempo...")
        return
    except regex.error as e:
        await m.reply_text(f"<b>Error:</b>\n<code>{e}</code>")
        return

    await m.reply_to_message.reply_text(f"{html.escape(res)}")


@Korone.on_message(
    filters.cmd(
        command="getsticker$",
        action="Obtenha o arquivo png de um sticker.",
    )
    & filters.reply
)
async def getsticker(c: Korone, m: Message):
    sticker = m.reply_to_message.sticker
    if sticker:
        if sticker.is_animated:
            await m.reply_text("Sticker animado não é suportado!")
        elif not sticker.is_animated:
            with tempfile.TemporaryDirectory() as tempdir:
                path = os.path.join(tempdir, "getsticker")
            sticker_file = await c.download_media(
                message=m.reply_to_message,
                file_name=f"{path}/{sticker.set_name}.png",
            )
            await m.reply_to_message.reply_document(
                document=sticker_file,
                caption=(
                    f"<b>Emoji:</b> {sticker.emoji}\n"
                    f"<b>Sticker ID:</b> <code>{sticker.file_id}</code>"
                ),
            )
            shutil.rmtree(tempdir, ignore_errors=True)
    else:
        await m.reply_text("Isso não é um sticker!")

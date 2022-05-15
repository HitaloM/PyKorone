# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2022 Amano Team

import base64
import binascii
import html
import os
import shutil
import tempfile
from datetime import datetime
from typing import Iterable

import httpx
import regex
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.errors import BadRequest, UserNotParticipant
from pyrogram.types import Message

from korone.bot import Korone
from korone.config import SUDOERS, SW_API
from korone.handlers import COMMANDS_HELP
from korone.handlers.utils.reddit import bodyfetcher, imagefetcher, titlefetcher
from korone.utils import http

GROUP = "general"

COMMANDS_HELP[GROUP] = {
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
            user = await c.get_users(args)
        elif m.reply_to_message:
            user = m.reply_to_message.from_user
        else:
            user = m.from_user
    except BadRequest as e:
        return await m.reply_text(f"<b>Error!</b>\n<code>{e}</code>")
    except IndexError:
        return await m.reply_text("Isso não me parece ser um usuário!")

    text = "<b>Informações do usuário</b>:"
    text += f"\nID: <code>{user.id}</code>"
    text += f"\nNome: <code>{html.escape(user.first_name)}</code>"

    if user.last_name:
        text += f"\nSobrenome: <code>{html.escape(user.last_name)}</code>"

    if user.username:
        text += f"\nNome de Usuário: @{html.escape(user.username)}"

    text += f"\nLink de Usuário: {user.mention(user.first_name, style='html')}"

    if user.photo:
        photo_count = await c.get_chat_photos_count(user.id)
        text += f"\nFotos de perfil: <code>{photo_count}</code>"

    if user.dc_id:
        text += f"\nDatacenter: <code>{user.dc_id}</code>"
    if user.language_code:
        text += f"\nIdioma: <code>{user.language_code}</code>"

    bio = (await c.get_chat(chat_id=user.id)).bio
    if bio:
        text += f"\n\n<b>Biografia:</b> <code>{html.escape(bio)}</code>"

    try:
        r = await http.get(
            f"https://api.spamwat.ch/banlist/{int(user.id)}",
            headers={"Authorization": f"Bearer {SW_API}"},
        )
        if r.status_code == 200:
            ban = r.json()
            text += "\n\nEste usuário está banido no @SpamWatch!"
            text += f"\nMotivo: <code>{ban['reason']}</code>"
    except httpx.HTTPError:
        pass

    try:
        member = await c.get_chat_member(chat_id=m.chat.id, user_id=user.id)
        if member.status == ChatMemberStatus.ADMINISTRATOR:
            text += "\n\nEste usuário é um <b>'administrador'</b> neste grupo."
        elif member.status == ChatMemberStatus.OWNER:
            text += "\n\nEste usuário é o <b>'criador'</b> deste grupo."
    except (UserNotParticipant, ValueError):
        pass

    if user.photo:
        async for photo in c.get_chat_photos(chat_id=user.id, limit=1):
            await m.reply_photo(
                photo=photo.file_id,
                caption=text,
                disable_notification=True,
            )
    else:
        await m.reply_text(text, disable_web_page_preview=True)


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
    if r.status_code != 200:
        return await m.reply_text(f"<b>Error!</b> <code>{r.status_code}</code>")
    caption = "Meow!! (^つωฅ^)"
    cat = r.json()
    if cat[0]["url"].endswith(".gif"):
        await m.reply_animation(cat[0]["url"], caption=caption)
    else:
        await m.reply_photo(cat[0]["url"], caption=caption)


@Korone.on_message(
    filters.cmd(command="dog", action="Imagens aleatórias de cachorros.")
)
async def dog_photo(c: Korone, m: Message):
    r = await http.get("https://dog.ceo/api/breeds/image/random")
    if r.status_code != 200:
        return await m.reply_text(f"<b>Error!</b> <code>{r.status_code}</code>")
    dog = r.json()
    await m.reply_photo(dog["message"], caption="Woof!! U・ᴥ・U")


@Korone.on_message(filters.cmd(command="fox", action="Imagens aleatórias de raposas."))
async def fox_photo(c: Korone, m: Message):
    r = await http.get("https://some-random-api.ml/img/fox")
    if r.status_code != 200:
        return await m.reply_text(f"<b>Error!</b> <code>{r.status_code}</code>")
    fox = r.json()
    await m.reply_photo(fox["link"], caption="What the fox say?")


@Korone.on_message(filters.cmd(command="panda", action="Imagens aleatórias de pandas."))
async def panda_photo(c: Korone, m: Message):
    r = await http.get("https://some-random-api.ml/img/panda")
    if r.status_code != 200:
        return await m.reply_text(f"<b>Error!</b> <code>{r.status_code}</code>")
    panda = r.json()
    await m.reply_photo(panda["link"], caption="🐼")


@Korone.on_message(
    filters.cmd(command="bird", action="Imagens aleatórias de pássaros.")
)
async def bird_photo(c: Korone, m: Message):
    r = await http.get("http://shibe.online/api/birds")
    if r.status_code != 200:
        return await m.reply_text(f"<b>Error!</b> <code>{r.status_code}</code>")
    bird = r.json()
    await m.reply_photo(bird[0], caption="🐦")


@Korone.on_message(
    filters.cmd(command="redpanda", action="Imagens aleatórias de pandas vermelhos.")
)
async def rpanda_photo(c: Korone, m: Message):
    r = await http.get("https://some-random-api.ml/img/red_panda")
    if r.status_code != 200:
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
        command=r"b64encode(\s(?P<text>.+))?",
        action=r"Codifique texto em base64.",
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
        command=r"b64decode(\s(?P<text>.+))?",
        action=r"Decodifique códigos base64.",
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


@Korone.on_message(
    filters.cmd(
        command=r"chat(\s(?P<text>.+))?",
        action="Retorna algumas informações do chat.",
    )
)
async def chat_info(c: Korone, m: Message):
    args = m.matches[0]["text"]
    CHAT_TYPES: Iterable[str] = ("channel", "group", "supergroup")

    try:
        chat = await c.get_chat(args) if args else await c.get_chat(m.chat.id)
    except BadRequest as e:
        await m.reply_text(f"<b>Erro!</b>\n<code>{e}</code>")
        return
    if chat.type not in CHAT_TYPES:
        await m.reply_text("Este chat é privado!")
        return

    if chat.type in CHAT_TYPES:
        text = "<b>Informações do chat</b>:\n"
        text += f"Nome: <code>{chat.title}</code>\n"
        text += f"ID: <code>{chat.id}</code>\n"
        if chat.username:
            text += f"Nome de Usuário: @{chat.username}\n"
        if chat.dc_id:
            text += f"Datacenter: <code>{chat.dc_id}</code>\n"
        text += f"Membros: <code>{chat.members_count}</code>\n"
        if chat.id == m.chat.id:
            text += f"Mensagens: <code>{m.id + 1}</code>\n"
        if chat.invite_link and m.from_user.id in SUDOERS:
            text += f"Link de Convite: {chat.invite_link}\n"
        if chat.description:
            text += f"\n<b>Descrição:</b>\n<code>{chat.description}</code>"

    await m.reply_text(text)
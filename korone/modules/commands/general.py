# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2022 Amano Team
#
# This file is part of Korone (Telegram Bot)

import base64
import binascii
import html
import os
import shutil
import tempfile
from datetime import datetime

import httpx
import regex
from pyrogram import filters
from pyrogram.errors import BadRequest, UserNotParticipant
from pyrogram.types import Message

from korone.config import SW_API
from korone.korone import Korone
from korone.modules import COMMANDS_HELP
from korone.utils import http
from korone.utils.args import get_args_str, need_args_dec
from korone.utils.reddit import bodyfetcher, imagefetcher, titlefetcher

GROUP = "general"

COMMANDS_HELP[GROUP] = {
    "description": "Este é meu módulo de comandos sem categoria.",
    "commands": {},
    "help": True,
}


@Korone.on_message(
    filters.cmd(
        command=r"ping", action=r"Verifique a velocidade de resposta do korone."
    )
)
async def ping(c: Korone, m: Message):
    first = datetime.now()
    sent = await m.reply_text("<b>Pong!</b>")
    second = datetime.now()
    time = (second - first).microseconds / 1000
    await sent.edit_text(f"<b>Pong!</b> <code>{time}</code>ms")


@Korone.on_message(
    filters.cmd(
        command=r"user",
        action=r"Retorna algumas informações do usuário.",
    )
)
async def user_info(c: Korone, m: Message):
    args = get_args_str(m)

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
        photo_count = await c.get_profile_photos_count(user.id)
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
        if member.status in ["administrator"]:
            text += "\n\nEste usuário é um <b>'administrador'</b> neste grupo."
        elif member.status in ["creator"]:
            text += "\n\nEste usuário é o <b>'criador'</b> deste grupo."
    except (UserNotParticipant, ValueError):
        pass

    if user.photo:
        photos = await c.get_profile_photos(user.id)
        await m.reply_photo(
            photo=photos[0].file_id,
            caption=text,
            disable_notification=True,
        )
    else:
        await m.reply_text(text, disable_web_page_preview=True)


@Korone.on_message(
    filters.cmd(
        command=r"file",
        action=r"Obtenha informações técnicas de uma mídia.",
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


@Korone.on_message(filters.cmd(command=r"cat", action=r"Imagens aleatórias de gatos."))
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
    filters.cmd(command=r"dog", action=r"Imagens aleatórias de cachorros.")
)
async def dog_photo(c: Korone, m: Message):
    r = await http.get("https://dog.ceo/api/breeds/image/random")
    if r.status_code != 200:
        return await m.reply_text(f"<b>Error!</b> <code>{r.status_code}</code>")
    dog = r.json()
    await m.reply_photo(dog["message"], caption="Woof!! U・ᴥ・U")


@Korone.on_message(
    filters.cmd(command=r"fox", action=r"Imagens aleatórias de raposas.")
)
async def fox_photo(c: Korone, m: Message):
    r = await http.get("https://some-random-api.ml/img/fox")
    if r.status_code != 200:
        return await m.reply_text(f"<b>Error!</b> <code>{r.status_code}</code>")
    fox = r.json()
    await m.reply_photo(fox["link"], caption="What the fox say?")


@Korone.on_message(
    filters.cmd(command=r"panda", action=r"Imagens aleatórias de pandas.")
)
async def panda_photo(c: Korone, m: Message):
    r = await http.get("https://some-random-api.ml/img/panda")
    if r.status_code != 200:
        return await m.reply_text(f"<b>Error!</b> <code>{r.status_code}</code>")
    panda = r.json()
    await m.reply_photo(panda["link"], caption="🐼")


@Korone.on_message(
    filters.cmd(command=r"bird", action=r"Imagens aleatórias de pássaros.")
)
async def bird_photo(c: Korone, m: Message):
    r = await http.get("http://shibe.online/api/birds")
    if r.status_code != 200:
        return await m.reply_text(f"<b>Error!</b> <code>{r.status_code}</code>")
    bird = r.json()
    await m.reply_photo(bird[0], caption="🐦")


@Korone.on_message(
    filters.cmd(command=r"redpanda", action=r"Imagens aleatórias de pandas vermelhos.")
)
async def rpanda_photo(c: Korone, m: Message):
    r = await http.get("https://some-random-api.ml/img/red_panda")
    if r.status_code != 200:
        return await m.reply_text(f"<b>Error!</b> <code>{r.status_code}</code>")
    rpanda = r.json()
    await m.reply_photo(rpanda["link"], caption="🐼")


@Korone.on_message(
    filters.cmd(
        command=r"red(?P<type>.)",
        action=r"Retorna tópicos do Reddit.",
        group=GROUP,
    )
)
async def redimg(c: Korone, m: Message):
    fetch_type = m.matches[0]["type"]
    sub = get_args_str(m)

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
        command=r"b64encode",
        action=r"Codifique texto em base64.",
    )
)
async def b64e(c: Korone, m: Message):
    text = get_args_str(m)
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
        command=r"b64decode",
        action=r"Decodifique códigos base64.",
    )
)
async def b64d(c: Korone, m: Message):
    text = get_args_str(m)
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
        command=r"getsticker",
        action=r"Obtenha o arquivo png de um sticker.",
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

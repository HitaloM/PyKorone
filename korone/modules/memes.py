# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

import html
import random

import httpx
from pyrogram import filters
from pyrogram.errors import BadRequest
from pyrogram.types import Message

from korone.bot import Korone
from korone.modules.utils.constants import PASTAMOJIS, REACTS
from korone.modules.utils.languages import get_strings_dec
from korone.modules.utils.messages import get_args, get_command


@Korone.on_message(filters.cmd(["neko", "waifu", "hug", "pat", "slap"]))
@get_strings_dec("memes")
async def neko_api(bot: Korone, message: Message, strings):
    command = get_command(message).lower()[1:].split("@")[0]
    async with httpx.AsyncClient(http2=True) as client:
        r = await client.get(f"https://nekos.life/api/v2/img/{command}")

    if r.status_code != 200:
        await message.reply_text(strings["api_error"])
        return

    image_url = (r.json())["url"]
    try:
        if message.reply_to_message:
            if command in ("neko", "waifu"):
                await message.reply_to_message.reply_photo(image_url)
            else:
                await message.reply_to_message.reply_document(image_url)
        elif command in ("neko", "waifu"):
            await message.reply_photo(image_url)
        else:
            await message.reply_document(image_url)
    except BadRequest:
        await message.reply_text(strings["badrequest_error"])
        return


@Korone.on_message(filters.cmd("vapor"))
@get_strings_dec("memes")
async def vapor(bot: Korone, message: Message, strings):
    text = get_args(message)
    reply = message.reply_to_message

    if not text and reply:
        if (reply.text or reply.caption) is not None:
            text = reply.text or reply.caption
        else:
            await message.reply_text(strings["need_text"])
            return

    if not text and not reply:
        await message.reply_text(strings["need_text"])
        return

    vapor = []
    for charac in text:
        if 0x21 <= ord(charac) <= 0x7F:
            vapor.append(chr(ord(charac) + 0xFEE0))
        elif ord(charac) == 0x20:
            vapor.append(chr(0x3000))
        else:
            vapor.append(charac)

    vaporized_text = "".join(vapor)
    try:
        if reply:
            await reply.reply_text(f"{html.escape(vaporized_text)}")
        else:
            await message.reply_text(f"{html.escape(vaporized_text)}")
    except BadRequest:
        return


@Korone.on_message(filters.cmd(["cp", "copypasta"]))
@get_strings_dec("memes")
async def copypasta(bot: Korone, message: Message, strings):
    text = get_args(message)
    reply = message.reply_to_message

    if not text and reply:
        if (reply.text or reply.caption) is not None:
            text = reply.text or reply.caption
        else:
            await message.reply_text(strings["need_text"])
            return

    if not text and not reply:
        await message.reply_text(strings["need_text"])
        return

    pasta = random.choice(PASTAMOJIS)
    try:
        b_char = random.choice(text).lower()
    except BaseException:
        return
    for owo in text:
        if owo == " ":
            pasta += random.choice(PASTAMOJIS)
        elif owo in PASTAMOJIS:
            pasta += owo
            pasta += random.choice(PASTAMOJIS)
        elif owo.lower() == b_char:
            pasta += "🅱️"
        else:
            pasta += owo.upper() if bool(random.getrandbits(1)) else owo.lower()

    pasta += random.choice(PASTAMOJIS)
    try:
        if reply:
            await reply.reply_text(f"{html.escape(pasta)}")
        else:
            await message.reply_text(f"{html.escape(pasta)}")
    except BadRequest:
        return


@Korone.on_message(filters.cmd("react"))
async def reacts(bot: Korone, message: Message):
    react = random.choice(REACTS)
    if message.reply_to_message:
        await message.reply_to_message.reply_text(react)
    else:
        await message.reply_text(react)


__help__ = True

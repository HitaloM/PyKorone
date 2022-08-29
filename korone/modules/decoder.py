# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo M. <https://github.com/HitaloM>

import base64
import binascii
import html
import unicodedata

from pyrogram import filters
from pyrogram.errors import MessageTooLong
from pyrogram.types import Message

from ..bot import Korone
from ..utils.disable import disableable_dec
from ..utils.languages import get_strings_dec
from ..utils.messages import get_args


@Korone.on_message(filters.cmd("chinfo"))
@disableable_dec("chinfo")
@get_strings_dec("decoder")
async def charinfo(bot: Korone, message: Message, strings):
    text = " ".join(get_args(message).split())
    if not text:
        await message.reply_text(strings["need_text"])
        return

    chars = []
    for char in text:
        preview = True

        try:
            name: str = unicodedata.name(char)
        except ValueError:
            name = "UNNAMED CONTROL CHARACTER"
            preview = False

        line = f"<code>U+{ord(char):04X}</code> {name}"
        if preview:
            line += f" <code>{char}</code>"

        chars.append(line)

    try:
        await message.reply_text("\n".join(chars))
    except MessageTooLong:
        await message.reply_text(strings["too_long_message"])


@Korone.on_message(filters.cmd("b64encode"))
@disableable_dec("b64encode")
@get_strings_dec("decoder")
async def b64e(bot: Korone, message: Message, strings):
    text = get_args(message)
    if not text:
        if message.reply_to_message:
            text = message.reply_to_message.text
        else:
            await message.reply_text(strings["need_text"])
            return

    b64 = base64.b64encode(text.encode("utf-8")).decode()
    await message.reply_text(f"<code>{b64}</code>")


@Korone.on_message(filters.cmd("b64decode"))
@disableable_dec("b64decode")
@get_strings_dec("decoder")
async def b64d(bot: Korone, message: Message, strings):
    text = get_args(message)
    if not text:
        if message.reply_to_message:
            text = message.reply_to_message.text
        else:
            await message.reply_text(strings["need_text"])
            return

    try:
        b64 = base64.b64decode(text).decode("utf-8", "replace")
    except binascii.Error as e:
        await message.reply_text(strings["invalid_b64"].format(error=e))
        return

    await message.reply_text(html.escape(b64))


__help__ = True

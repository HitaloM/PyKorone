# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

import base64
import binascii
import html

from pyrogram import filters
from pyrogram.types import Message

from korone.bot import Korone
from korone.modules.utils.languages import get_strings_dec
from korone.modules.utils.messages import get_args_str


@Korone.on_message(filters.cmd("b64encode"))
@get_strings_dec("utilities")
async def b64e(bot: Korone, message: Message, strings):
    text = get_args_str(message)
    if not text:
        if message.reply_to_message:
            text = message.reply_to_message.text
        else:
            await message.reply_text(strings["need_text"])
            return

    b64 = base64.b64encode(text.encode("utf-8")).decode()
    await message.reply_text(f"<code>{b64}</code>")


@Korone.on_message(filters.cmd("b64decode"))
@get_strings_dec("utilities")
async def b64d(bot: Korone, message: Message, strings):
    text = get_args_str(message)
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

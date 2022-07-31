# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

import base64
import binascii
import html

from pyrogram import filters
from pyrogram.types import Message

from korone.bot import Korone
from korone.modules.utils.images import stickcolorsync
from korone.modules.utils.languages import get_strings_dec
from korone.modules.utils.messages import get_args, need_args_dec
from korone.utils.aioify import run_async


@Korone.on_message(filters.cmd("b64encode"))
@get_strings_dec("utilities")
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
@get_strings_dec("utilities")
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


@Korone.on_message(filters.cmd("color"))
@need_args_dec()
@get_strings_dec("utilities")
async def color_sticker(bot: Korone, message: Message, strings):
    color = get_args(message)

    if color_sticker:
        await message.reply_sticker(
            sticker=await run_async(
                stickcolorsync,
                color,
            )
        )
    else:
        await message.reply_text(
            strings["invalid_color"].format(color=color),
        )


__help__ = True

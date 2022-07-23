# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo

from pyrogram import filters
from pyrogram.types import Message

from korone.bot import Korone


@Korone.on_message(filters.cmd("start"))
async def start(bot: Korone, message: Message):
    await message.reply_text("Hello, I'm Korone!")

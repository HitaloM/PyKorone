# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

from pyrogram import filters
from pyrogram.types import Message

from korone.bot import Korone
from korone.modules.utils.languages import get_strings_dec


@Korone.on_message(filters.cmd("start"))
@get_strings_dec("pm_menu")
async def start(bot: Korone, message: Message, strings):
    await message.reply_text(strings["start_text"])

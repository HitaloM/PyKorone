# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo

import datetime
import platform

import humanize
import psutil
from pyrogram import filters
from pyrogram.types import Message

from korone.bot import Korone


@Korone.on_message(filters.cmd("stats"))
async def stats(bot: Korone, message: Message):
    text = "\n<b>System</b>"
    uname = platform.uname()
    text += f"\n    <b>OS</b>: <code>{uname.system}</code>"
    text += f"\n    <b>Node</b>: <code>{uname.node}</code>"
    text += f"\n    <b>Kernel</b>: <code>{uname.release}</code>"
    text += f"\n    <b>Architecture</b>: <code>{uname.machine}</code>"
    memory = psutil.virtual_memory()
    text += f"\n    <b>Memory</b>: <code>{humanize.naturalsize(memory.used, binary=True)}/{humanize.naturalsize(memory.total, binary=True)}</code>"
    now = datetime.datetime.now().replace(tzinfo=datetime.timezone.utc)
    date = now - bot.start_datetime
    text += f"\n    <b>UPTime</b>: <code>{humanize.precisedelta(date)}</code>"

    await message.reply_text(text)

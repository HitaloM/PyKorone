# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

import datetime
import os
import platform
import shutil

import humanize
import psutil
from pyrogram import filters
from pyrogram.types import Message

from korone.bot import Korone
from korone.database import database
from korone.database.chats import filter_chats_by_language
from korone.database.users import filter_users_by_language
from korone.modules.utils.languages import LANGUAGES

conn = database.get_conn()


@Korone.on_message(filters.cmd("stats"))
async def stats(bot: Korone, message: Message):
    text = "<b>Database</b>"
    text += f"\n    <b>Size</b>: <code>{humanize.naturalsize(os.stat('./korone/database/db.sqlite').st_size, binary=True)}</code>"
    disk = shutil.disk_usage("/")
    text += (
        f"\n    <b>Free</b>: <code>{humanize.naturalsize(disk[2], binary=True)}</code>"
    )
    text += "\n<b>Chats</b>"
    users_count = await conn.execute("select count() from users")
    users_count = await users_count.fetchone()
    text += f"\n    <b>Users</b>: <code>{users_count[0]}</code>"
    for lang in LANGUAGES.values():
        language = lang["language_info"]
        users = await filter_users_by_language(language=language["code"])
        text += (
            f"\n        <b>{language['code'].upper()}</b>: <code>{len(users)}</code>"
        )
    groups_count = await conn.execute("select count() from chats")
    groups_count = await groups_count.fetchone()
    text += f"\n    <b>Groups</b>: <code>{groups_count[0]}</code>"
    for lang in LANGUAGES.values():
        language = lang["language_info"]
        groups = await filter_chats_by_language(language=language["code"])
        text += (
            f"\n        <b>{language['code'].upper()}</b>: <code>{len(groups)}</code>"
        )
    text += "\n<b>System</b>"
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

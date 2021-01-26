# This file is part of Korone (Telegram Bot)

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as
# published by the Free Software Foundation, either version 3 of the
# License, or (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import platform
import random
import re
from datetime import datetime

import kantex
import pyrogram
import pyromod
from config import prefix
from kantex.html import (Bold, Code, KanTeXDocument, KeyValueItem, Section,
                         SubSection)
from pyrogram import Client, filters
from pyrogram.types import Message

from handlers.utils.random import NONE_CMD


@Client.on_message(filters.command("ping", prefix))
async def ping(c: Client, m: Message):
    first = datetime.now()
    sent = await m.reply_text("<b>Pong!</b>")
    second = datetime.now()
    time = (second - first).microseconds / 1000
    await sent.edit_text(f"<b>Pong!</b> <code>{time}</code>ms")


@Client.on_message(filters.command("user", prefix) & filters.reply)
async def user_info(c: Client, m: Message):
    user_id = m.reply_to_message.from_user.id
    first_name = m.reply_to_message.from_user.first_name
    try:
        last_name = m.reply_to_message.from_user.last_name
    except Exception:
        last_name = None
    username = m.reply_to_message.from_user.username
    doc = KanTeXDocument(
        Section(first_name,
                SubSection('Geral',
                           KeyValueItem('id', Code(user_id)),
                           KeyValueItem('first_name', Code(first_name)),
                           KeyValueItem('last_name', Code(last_name)),
                           KeyValueItem('username', Code(username)))))
    await m.reply_text(doc)


@Client.on_message(filters.command("copy", prefix))
async def copy(c: Client, m: Message):
    await c.copy_message(
        chat_id=m.chat.id,
        from_chat_id=m.chat.id,
        message_id=m.reply_to_message.message_id
    )


@Client.on_message(filters.command("py", prefix))
async def dev(c: Client, m: Message):
    source_url = "git.io/JtmRH"
    doc = Section("PyKorone Bot",
                  KeyValueItem(Bold('Source'), source_url),
                  KeyValueItem(Bold('Pyrogram version'), pyrogram.__version__),
                  KeyValueItem(Bold('Pyromod version'), pyromod.__version__),
                  KeyValueItem(Bold('Python version'), platform.python_version()),
                  KeyValueItem(Bold('KanTeX version'), kantex.__version__),
                  KeyValueItem(Bold('System version'), c.system_version))
    await m.reply_text(doc, disable_web_page_preview=True)


@Client.on_message(filters.regex(r"^/\w+") & filters.private, group=-1)
async def none_command(c: Client, m: Message):
    if re.match(r"^(\/start|\/py|\/ping|\/copy|\/help|\/reboot|\/copy|\/upgrade|\/shutdown|korone,)", m.text):
        m.continue_propagation()
    react = random.choice(NONE_CMD)
    await m.reply_text(react)

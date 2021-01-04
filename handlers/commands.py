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

import re
import platform
import random
from datetime import datetime

import pyromod
import pyrogram
from pyrogram import Client, filters
from pyrogram.types import Message
from pyromod.helpers import ikb

from config import prefix
from handlers.utils.random import NONE_CMD


@Client.on_message(filters.command("ping", prefix))
async def ping(c: Client, m: Message):
    first = datetime.now()
    sent = await m.reply_text("<b>Pong!</b>")
    second = datetime.now()
    time = (second - first).microseconds / 1000
    await sent.edit_text(f"<b>Pong!</b> <code>{time}</code>ms")


@Client.on_message(filters.command("py", prefix))
async def dev(c: Client, m: Message):
    python_version = platform.python_version()
    pyrogram_version = pyrogram.__version__
    await m.reply_text(
        f"""
<b>Korone Info:</b>
- <b>Pyrogram:</b> <code>v{pyrogram.__version__}</code>
- <b>Pyromod:</b> <code>v{pyromod.__version__}</code>
- <b>Python:</b> <code>v{platform.python_version()}</code>
- <b>System:</b> <code>{c.system_version}</code>

Feito com ❤️ por @Hitalo
    """
    )


@Client.on_message(filters.command("start", prefix))
async def start(c: Client, m: Message):
    keyboard = ikb([
        [('Grupo Off-Topic', 'https://t.me/SpamTherapy', 'url')]])
    await m.reply_text("Oi, eu sou o <b>Korone</b>, um bot interativo que adora participar de grupos!", reply_markup=keyboard)


@Client.on_message(filters.regex(r'^/\w+') & filters.private, group=-1)
async def none_command(c: Client, m: Message):
    if re.match(r'^(\/start|\/py|\/ping|\/reboot|\/shutdown|korone,)', m.text):
        m.continue_propagation()
    react = random.choice(NONE_CMD)
    await m.reply_text(react)

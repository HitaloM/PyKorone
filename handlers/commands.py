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
import pyrogram
from datetime import datetime

from pyrogram import Client, filters
from pyrogram.types import Message

from config import prefix


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
- <b>Pyrogram:</b> <code>{c.app_version}</code>
- <b>Python:</b> <code>{c.device_model}</code>
- <b>System:</b> <code>{c.system_version}</code>

Feito com ❤️ por @Hitalo
    """
    )


@Client.on_message(filters.command("start", prefix))
async def start(c: Client, m: Message):
    await m.reply_text(
        """
Oi, eu sou o <b>Korone</b>, um bot interativo que adora participar de grupos!

Você pode entender como eu funciono com o comando /help
    """
    )

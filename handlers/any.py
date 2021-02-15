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

from database import Chats
from pyrogram import Client, filters
from pyrogram.types import Message

from config import prefix

from . import COMMANDS_HELP


@Client.on_message(filters.edited)
async def reject(c: Client, m: Message):
    m.stop_propagation()


def int_filter(filter, group: str = "others", action: str = None, *args, **kwargs):
    COMMANDS_HELP[group]["filters"][filter] = {"action": action or " "}
    return filters.regex(r"(?i)^{0}(\.|\?|\!)?$".format(filter), *args, **kwargs)


filters.int = int_filter


def command_filter(
    command, group: str = "general", action: str = None, *args, **kwargs
):
    if command not in COMMANDS_HELP[group]["commands"].keys():
        COMMANDS_HELP[group]["commands"][command] = {"action": action or ""}
    prefixes = "".join(prefix)
    _prefix = f"^[{re.escape(prefixes)}]"
    return filters.regex(_prefix + command, *args, **kwargs)


filters.cmd = command_filter


@Client.on_message(~filters.private & filters.all)
async def on_all_m(c: Client, m: Message):
    if await Chats.filter(id=m.chat.id):
        pass
    else:
        await Chats.create(id=m.chat.id, title=m.chat.title)
    m.continue_propagation()

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

from pyrogram import Client, filters
from pyrogram.types import Message

from config import prefix


@Client.on_message(filters.edited)
async def reject(c: Client, m: Message):
    m.stop_propagation()


def command_filter(command, *args, **kwargs):
    prefixes = ''.join(prefix)
    _prefix = f"^[{re.escape(prefixes)}]"
    return filters.regex(_prefix+command, *args, **kwargs)
    
filters.cmd = command_filter

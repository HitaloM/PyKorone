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


from pyrogram import Client, filters
from pyrogram.types import Message

from utils import sw


@Client.on_message(filters.new_chat_members)
async def greetings(c: Client, m: Message):
    try:
        if sw is not None:
            sw_ban = sw.get_ban(m.reply_to_message.from_user.id)
            if sw_ban:
                r = sw_ban.reason
                fn = m.reply_to_message.from_user.first_name
                await m.reply_text(
                    f"O usuário <code>{fn}</code> está banido na @SpamWatch e por isso foi removido!\nMotivo: <code>{r}</code>"
                )
    except BaseException:
        pass

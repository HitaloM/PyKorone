# This file is part of Korone (Telegram Bot)
# Copyright (C) 2021 AmanoTeam

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

from kantex.html import KanTeXDocument, Section, KeyValueItem, Bold, Code
from utils import sw


@Client.on_message(filters.new_chat_members)
async def greetings(c: Client, m: Message):
    try:
        if sw is not None:
            sw_ban = sw.get_ban(m.reply_to_message.from_user.id)
            if sw_ban:
                reason = sw_ban.reason
                user = m.reply_to_message.from_user
                try:
                    await c.kick_chat_member(m.chat.id, user.id)
                except BadRequest:
                    return
                doc = KanTeXDocument(
                    Section(
                        Bold("@SpamWatch Ban"),
                        KeyValueItem(
                            Bold("User"),
                            f"{Mention(user.first_name, user.id)} [{Code(user.id)}]",
                        ),
                        KeyValueItem(Bold("Reason"), Code(reason)),
                    )
                )
                await m.reply_text(doc)
    except BaseException:
        pass

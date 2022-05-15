# This file is part of Korone (Telegram Bot)
# Copyright (C) 2022 AmanoTeam

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

import html

from pyrogram import filters
from pyrogram.types import (
    InlineQuery,
    InlineQueryResultArticle,
    InputTextMessageContent,
    Message,
)

from korone.korone import Korone


@Korone.on_edited_message()
async def reject_edited(c: Korone, m: Message):
    m.stop_propagation()


@Korone.on_message(filters.new_chat_members)
async def thanks_for(c: Korone, m: Message):
    if c.me.id in [x.id for x in m.new_chat_members]:
        await c.send_message(
            chat_id=m.chat.id,
            text=("Obrigado por me adicionar em seu grupo!"),
            disable_notification=True,
        )
        await c.send_log(
            text=(
                f"Eu fui adicionado ao grupo <b>{html.escape(m.chat.title)}</b>"
                f" (<code>{m.chat.id}</code>)."
            ),
            disable_notification=False,
            disable_web_page_preview=True,
        )

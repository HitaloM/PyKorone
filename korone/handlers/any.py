# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2022 Amano Team

import html

from pyrogram import filters
from pyrogram.types import Message

from korone.bot import Korone


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

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from datetime import UTC, datetime

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.types import CallbackQuery, Message

from korone.decorators import router
from korone.filters import Command, IsSudo
from korone.modules.sudo.callback_data import PingCallbackData


@router.message(Command("ping", disableable=False) & IsSudo)
@router.callback_query(PingCallbackData.filter() & IsSudo)
async def ping_command(client: Client, event: Message | CallbackQuery) -> None:
    keyboard = InlineKeyboardBuilder()
    keyboard.button(text="Retry", callback_data=PingCallbackData())

    first = datetime.now(UTC)
    if isinstance(event, Message):
        message = await event.reply("<b>Pong!</b>")
    else:
        message = event.message
        await message.edit("<b>Pong!</b>")

    second = datetime.now(UTC)
    await message.edit(
        f"<b>Pong!</b> <code>{(second - first).microseconds / 1000}</code>ms",
        reply_markup=keyboard.as_markup(),
    )

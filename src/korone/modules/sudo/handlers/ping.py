# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from datetime import UTC, datetime

from hydrogram import Client
from hydrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from korone.decorators import router
from korone.filters import Command, IsSudo
from korone.modules.sudo.callback_data import PingCallbackData


@router.message(Command("ping", disableable=False) & IsSudo)
@router.callback_query(PingCallbackData.filter() & IsSudo)
async def ping_command(client: Client, update: Message | CallbackQuery) -> None:
    first = datetime.now(UTC)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(text="Retry", callback_data=PingCallbackData().pack())]
    ])

    match update:
        case Message():
            message = await update.reply("<b>Pong!</b>")
        case CallbackQuery():
            message = update.message
            await message.edit("<b>Pong!</b>")

    second = datetime.now(UTC)
    await message.edit(
        f"<b>Pong!</b> <code>{(second - first).microseconds / 1000}</code>ms",
        reply_markup=keyboard,
    )

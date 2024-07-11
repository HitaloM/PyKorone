# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from datetime import UTC, datetime

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.types import CallbackQuery, Message

from korone.decorators import router
from korone.filters import Command, IsSudo
from korone.handlers.abstract import CallbackQueryHandler, MessageHandler
from korone.modules.sudo.callback_data import PingCallbackData


class PingBase:
    @staticmethod
    async def _send_ping_response(client: Client, message: Message, edit: bool = False) -> None:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text="Retry", callback_data=PingCallbackData())

        first = datetime.now(UTC)
        if edit:
            await message.edit("<b>Pong!</b>")
        else:
            message = await message.reply("<b>Pong!</b>")
        second = datetime.now(UTC)
        await message.edit(
            f"<b>Pong!</b> <code>{(second - first).microseconds / 1000}</code>ms",
            reply_markup=keyboard.as_markup(),
        )


class Ping(MessageHandler, PingBase):
    @router.message(Command("ping", disableable=False) & IsSudo)
    async def handle(self, client: Client, message: Message) -> None:
        await self._send_ping_response(client, message)


class PingRetry(CallbackQueryHandler, PingBase):
    @router.callback_query(PingCallbackData.filter() & IsSudo)
    async def handle(self, client: Client, callback: CallbackQuery) -> None:
        await self._send_ping_response(client, callback.message, edit=True)

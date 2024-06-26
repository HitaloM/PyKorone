# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from contextlib import suppress

from hydrogram import Client
from hydrogram.errors import MessageNotModified
from hydrogram.types import CallbackQuery

from korone.decorators import router
from korone.handlers.abstract import CallbackQueryHandler
from korone.modules.gsm_arena.callback_data import GetDeviceCallback
from korone.modules.gsm_arena.utils import check_phone_details, format_phone


class GetGSMArena(CallbackQueryHandler):
    @staticmethod
    @router.callback_query(GetDeviceCallback.filter())
    async def handle(client: Client, callback: CallbackQuery) -> None:
        if not callback.data:
            return

        query: str = GetDeviceCallback.unpack(callback.data).device
        phone = await check_phone_details(query)

        with suppress(MessageNotModified):
            await callback.edit_message_text(text=format_phone(phone))

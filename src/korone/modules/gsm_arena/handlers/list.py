# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from contextlib import suppress

from hydrogram import Client
from hydrogram.errors import MessageNotModified
from hydrogram.types import CallbackQuery

from korone.decorators import router
from korone.handlers.abstract import CallbackQueryHandler
from korone.modules.gsm_arena.callback_data import DevicePageCallback
from korone.modules.gsm_arena.utils import create_pagination_layout, search_phone


class ListGSMArena(CallbackQueryHandler):
    @staticmethod
    @router.callback_query(DevicePageCallback.filter())
    async def handle(client: Client, callback: CallbackQuery) -> None:
        if not callback.data:
            return

        query: str = DevicePageCallback.unpack(callback.data).device
        page: int = DevicePageCallback.unpack(callback.data).page

        devices = await search_phone(query)
        keyboard = create_pagination_layout(devices, query, page)
        with suppress(MessageNotModified):
            await callback.edit_message_reply_markup(keyboard.as_markup())

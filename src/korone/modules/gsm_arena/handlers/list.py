# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from contextlib import suppress

from hydrogram import Client
from hydrogram.errors import MessageNotModified
from hydrogram.types import CallbackQuery

from korone.decorators import router
from korone.modules.gsm_arena.callback_data import DevicePageCallback
from korone.modules.gsm_arena.utils.keyboard import create_pagination_layout
from korone.modules.gsm_arena.utils.scraper import search_phone


@router.callback_query(DevicePageCallback.filter())
async def list_gsmarena_callback(client: Client, callback: CallbackQuery) -> None:
    if not callback.data:
        return

    callback_data = DevicePageCallback.unpack(callback.data)
    query, page = callback_data.device, callback_data.page

    devices = await search_phone(query)
    keyboard = create_pagination_layout(devices, query, page)

    with suppress(MessageNotModified):
        await callback.edit_message_reply_markup(keyboard)

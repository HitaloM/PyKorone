# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from contextlib import suppress

from hydrogram import Client
from hydrogram.errors import MessageNotModified
from hydrogram.types import CallbackQuery

from korone.decorators import router
from korone.modules.gsm_arena.callback_data import DevicePageCallback
from korone.modules.gsm_arena.utils import create_pagination_layout, search_phone


@router.callback_query(DevicePageCallback.filter())
async def list_gsmarena_callback(client: Client, callback: CallbackQuery) -> None:
    if not callback.data:
        return

    query, page = unpack_callback_data(callback.data)
    devices = await search_phone(query)
    keyboard = create_pagination_layout(devices, query, page)

    with suppress(MessageNotModified):
        await callback.edit_message_reply_markup(keyboard.as_markup())


def unpack_callback_data(data: str | bytes) -> tuple[str, int]:
    callback_data = DevicePageCallback.unpack(data)
    return callback_data.device, callback_data.page

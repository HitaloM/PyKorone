# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from contextlib import suppress

from hydrogram import Client
from hydrogram.enums import ChatType
from hydrogram.errors import MessageNotModified
from hydrogram.types import CallbackQuery

from korone.decorators import router
from korone.modules.gsm_arena.callback_data import GetDeviceCallback
from korone.modules.gsm_arena.utils.scraper import check_phone_details, format_phone


@router.callback_query(GetDeviceCallback.filter())
async def get_gsmarena_callback(client: Client, callback: CallbackQuery) -> None:
    if not callback.data:
        return

    query = GetDeviceCallback.unpack(callback.data).device
    phone = await check_phone_details(query)
    formatted_phone = format_phone(phone)

    if callback.message.chat.type == ChatType.PRIVATE:
        await callback.message.reply(text=formatted_phone)
        return

    with suppress(MessageNotModified):
        await callback.edit_message_text(text=formatted_phone)

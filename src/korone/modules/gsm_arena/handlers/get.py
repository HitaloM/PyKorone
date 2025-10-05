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
from korone.utils.i18n import gettext as _
from korone.utils.logging import get_logger

logger = get_logger(__name__)


@router.callback_query(GetDeviceCallback.filter())
async def get_gsmarena_callback(client: Client, callback: CallbackQuery) -> None:
    if not callback.data:
        await callback.answer(_("Invalid callback data"), show_alert=True)
        return

    try:
        query = GetDeviceCallback.unpack(callback.data).device
        await callback.answer(_("Fetching device details..."))

        phone = await check_phone_details(query)

        if not phone:
            await callback.answer(_("Error fetching device details"), show_alert=True)
            return

        formatted_phone = format_phone(phone)

        if callback.message.chat.type == ChatType.PRIVATE:
            await callback.message.reply(text=formatted_phone)
            return

        with suppress(MessageNotModified):
            await callback.edit_message_text(text=formatted_phone)
    except Exception as e:
        await logger.aerror("[GSM Arena] Error handling get device callback: %s", str(e))
        await callback.answer(_("An error occurred. Please try again."), show_alert=True)

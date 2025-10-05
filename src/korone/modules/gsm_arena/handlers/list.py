# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from contextlib import suppress

from hydrogram import Client
from hydrogram.errors import MessageNotModified
from hydrogram.types import CallbackQuery

from korone.decorators import router
from korone.modules.gsm_arena.callback_data import DevicePageCallback
from korone.modules.gsm_arena.utils.keyboard import create_pagination_layout
from korone.modules.gsm_arena.utils.scraper import search_phone
from korone.utils.i18n import gettext as _
from korone.utils.logging import get_logger

logger = get_logger(__name__)


@router.callback_query(DevicePageCallback.filter())
async def list_gsmarena_callback(client: Client, callback: CallbackQuery) -> None:
    if not callback.data:
        await callback.answer(_("Invalid callback data"), show_alert=True)
        return

    try:
        callback_data = DevicePageCallback.unpack(callback.data)
        query, page = callback_data.device, callback_data.page

        devices = await search_phone(query)

        if not devices:
            await callback.answer(_("No devices found"), show_alert=True)
            return

        keyboard = create_pagination_layout(devices, query, page)

        with suppress(MessageNotModified):
            await callback.edit_message_reply_markup(keyboard)

        await callback.answer()
    except Exception as e:
        await logger.aerror("[GSM Arena] Error handling list callback: %s", str(e))
        await callback.answer(_("An error occurred. Please try again."), show_alert=True)

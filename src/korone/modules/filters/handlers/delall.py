# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.types import CallbackQuery, Message
from magic_filter import F

from korone.decorators import router
from korone.filters import Command, IsAdmin
from korone.modules.filters.callback_data import DeleteAllFiltersCallback
from korone.modules.filters.database import delete_all_filters, update_filters_cache
from korone.utils.i18n import gettext as _


@router.message(Command("delallfilters") & IsAdmin)
async def delallfilters_command(client: Client, message: Message) -> None:
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text=_("✅ Confirm Deletion"),
        callback_data=DeleteAllFiltersCallback(action="confirm").pack(),
    )
    keyboard.button(
        text=_("❌ Cancel"),
        callback_data=DeleteAllFiltersCallback(action="cancel").pack(),
    )
    keyboard.adjust(2)
    await message.reply(
        _("⚠️ Are you sure you want to delete all filters? This action cannot be undone."),
        reply_markup=keyboard.as_markup(),
    )


@router.callback_query(DeleteAllFiltersCallback.filter(F.action.in_(["confirm", "cancel"])))
async def delallfilters_cb(client: Client, callback: CallbackQuery) -> None:
    if not callback.data:
        return

    chat_id = callback.message.chat.id
    action = DeleteAllFiltersCallback.unpack(callback.data).action

    match action:
        case "confirm":
            await delete_all_filters(chat_id)
            await update_filters_cache(chat_id)
            await callback.message.edit(_("All filters have been deleted."))
        case "cancel":
            await callback.message.edit(_("Deletion of all filters has been canceled."))

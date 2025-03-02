# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.types import CallbackQuery, Message
from magic_filter import F

from korone.decorators import router
from korone.filters import Command, UserIsAdmin
from korone.modules.filters.callback_data import DelAllFiltersAction, DelAllFiltersCallback
from korone.modules.filters.database import delete_all_filters, update_filters_cache
from korone.utils.i18n import gettext as _


@router.message(Command("delallfilters") & UserIsAdmin)
async def delallfilters_command(client: Client, message: Message) -> None:
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text=_("✅ Confirm Deletion"),
        callback_data=DelAllFiltersCallback(action=DelAllFiltersAction.Confim),
    )
    keyboard.button(
        text=_("❌ Cancel"),
        callback_data=DelAllFiltersCallback(action=DelAllFiltersAction.Cancel),
    )
    keyboard.adjust(2)

    await message.reply(
        _("⚠️ Are you sure you want to delete all filters? This action cannot be undone."),
        reply_markup=keyboard.as_markup(),
    )


@router.callback_query(
    DelAllFiltersCallback.filter(
        F.action.in_([
            DelAllFiltersAction.Cancel,
            DelAllFiltersAction.Confim,
        ])
    )
)
async def delallfilters_cb(client: Client, callback: CallbackQuery) -> None:
    if not callback.data:
        return

    callback_data = DelAllFiltersCallback.unpack(callback.data)
    message = callback.message

    if callback_data.action == DelAllFiltersAction.Confim:
        chat_id = message.chat.id
        if not await delete_all_filters(chat_id):
            await message.edit(_("There are no filters to delete."))
            return

        await update_filters_cache(chat_id)
        await message.edit(_("All filters have been deleted."))
        return

    if callback_data.action == DelAllFiltersAction.Cancel:
        await message.edit(_("Deletion of all filters has been canceled."))
        return

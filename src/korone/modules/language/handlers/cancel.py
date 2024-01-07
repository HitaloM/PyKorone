# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client, filters
from hydrogram.types import CallbackQuery

from korone.decorators import on_callback_query
from korone.handlers.callback_query_handler import CallbackQueryHandler
from korone.utils.i18n import gettext as _


class ChangeLanguageCancel(CallbackQueryHandler):
    @on_callback_query(filters.regex(r"^cancellanguage$"))
    async def handle(self, client: Client, callback: CallbackQuery):
        await callback.message.edit_text(
            _(
                "Changing language was canceled, you can change language again "
                "by using /language command."
            )
        )

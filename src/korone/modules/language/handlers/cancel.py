# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.types import CallbackQuery
from magic_filter import F

from korone.client import Korone
from korone.handlers.callback_query_handler import CallbackQueryHandler
from korone.modules.language.callback_data import LangMenuCallback
from korone.utils.i18n import gettext as _


class ChangeLanguageCancel(CallbackQueryHandler):
    @Korone.on_callback_query(LangMenuCallback.filter(F.menu == "cancel"))
    async def handle(self, client: Client, callback: CallbackQuery):
        await callback.message.edit_text(
            _(
                "Changing language was canceled, you can change language again "
                "by using /language command."
            )
        )

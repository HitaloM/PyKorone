# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from hairydogm.i18n import gettext as _
from hydrogram import Client, filters
from hydrogram.enums import ChatType
from hydrogram.types import CallbackQuery
from korone.database.impl import SQLite3Connection
from korone.decorators import on_callback_query
from korone.handlers.callback_query_handler import CallbackQueryHandler
from korone.modules.language.manager import ChatLanguageManager
from korone.modules.manager import Table


class ApplyLanguage(CallbackQueryHandler):
    @on_callback_query(filters.regex(r"^setlang:(?P<language>.*)$"))
    async def handle(self, client: Client, callback: CallbackQuery):
        if not callback.matches:
            return await callback.answer(_("Something went wrong."))

        is_private = callback.message.chat.type == ChatType.PRIVATE

        language = callback.matches[0].group("language")
        async with SQLite3Connection() as conn:
            db = ChatLanguageManager(conn, Table.USERS if is_private else Table.GROUPS)
            await db.set_chat_language(
                callback.from_user.id if is_private else callback.message.chat.id,
                language,
            )

        text = _("Language changed to {new_lang}.").format(new_lang=language)

        await callback.message.edit_text(text)
        return None

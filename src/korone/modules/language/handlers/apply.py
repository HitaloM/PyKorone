# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client, filters
from hydrogram.enums import ChatType
from hydrogram.types import CallbackQuery
from korone.database.impl import SQLite3Connection
from korone.decorators import on_callback_query
from korone.handlers.callback_query_handler import CallbackQueryHandler
from korone.modules.language.manager import ChatLanguageManager
from korone.modules.manager import Table
from korone.utils.i18n import get_i18n
from korone.utils.i18n import gettext as _


class ApplyLanguage(CallbackQueryHandler):
    @on_callback_query(filters.regex(r"^setlang:(?P<language>.*)$"))
    async def handle(self, client: Client, callback: CallbackQuery) -> None:
        if not callback.matches:
            await callback.answer(_("Something went wrong."))
            return

        is_private = callback.message.chat.type == ChatType.PRIVATE
        language: str = callback.matches[0].group("language")

        await self.set_chat_language(is_private, callback, language)
        text, keyboard = await self.prepare_response(language)

        await callback.message.edit_text(
            text,
            reply_markup=keyboard.as_markup() if keyboard else None,  # type: ignore
            disable_web_page_preview=True,
        )

    async def set_chat_language(
        self, is_private: bool, callback: CallbackQuery, language: str
    ) -> None:
        async with SQLite3Connection() as conn:
            db = ChatLanguageManager(conn, Table.USERS if is_private else Table.GROUPS)
            await db.set_chat_language(
                callback.from_user.id if is_private else callback.message.chat.id,
                language,
            )

    async def prepare_response(self, language: str) -> tuple[str, InlineKeyboardBuilder | None]:
        i18n = get_i18n()
        text = _("Language changed to {new_lang}.", locale=language).format(new_lang=language)

        keyboard = None
        if stats := i18n.get_locale_stats(locale_code=language):
            percent = 100 if i18n.default_locale == language else stats.percent_translated
            text += _(
                "\nThe language is {percent}% translated.",
                locale=language,
            ).format(percent=percent)
            if percent > 99:
                text += _(
                    "\nIn case you find any errors, please file a issue in the {link}.",
                    locale=language,
                ).format(
                    link="<a href='https://github.com/HitaloM/PyKorone/issues'>GitHub Repo</a>"
                )
            else:
                text += _(
                    "\nPlease help us translate this language by completing it on "
                    "the Crowdin website.",
                    locale=language,
                )
                keyboard = InlineKeyboardBuilder()
                keyboard.button(
                    text=_("🌍 Open Crowdin", locale=language),
                    url="https://crowdin.com/project/pykorone",
                )

        return text, keyboard

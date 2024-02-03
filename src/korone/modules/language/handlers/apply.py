# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.enums import ChatType
from hydrogram.types import CallbackQuery

from korone.constants import CROWDIN_URL, GITHUB_URL
from korone.database.impl import SQLite3Connection
from korone.database.query import Query
from korone.database.table import Document
from korone.decorators import router
from korone.handlers.callback_query_handler import CallbackQueryHandler
from korone.modules.language.callback_data import SetLangCallback
from korone.utils.i18n import get_i18n
from korone.utils.i18n import gettext as _


class ApplyLanguage(CallbackQueryHandler):
    crowdin_url: str = CROWDIN_URL
    github_url: str = f"{GITHUB_URL}/issues"

    @router.callback_query(SetLangCallback.filter())
    async def handle(self, client: Client, callback: CallbackQuery) -> None:
        if not callback.data:
            await callback.answer(_("Something went wrong."))
            return

        is_private = callback.message.chat.type == ChatType.PRIVATE
        language: str = SetLangCallback.unpack(callback.data).lang

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
            table = await conn.table("Users" if is_private else "Groups")
            query = Query()
            await table.update(Document(language=language), query.id == callback.message.chat.id)

    async def prepare_response(self, language: str) -> tuple[str, InlineKeyboardBuilder | None]:
        i18n = get_i18n()
        text = _("Language changed to {new_lang}.", locale=language).format(
            new_lang=i18n.locale_display(i18n.babel(language))
        )

        keyboard = None
        if language == i18n.default_locale:
            keyboard = InlineKeyboardBuilder()
            text += _(
                "\nThis is the bot's native language."
                "\nIf you find any errors, please file a issue in the "
                "GitHub Repository.",
                locale=language,
            )
            keyboard.button(
                text=_("🐞 Open GitHub", locale=language),
                url=self.github_url,
            )

        elif stats := i18n.get_locale_stats(locale_code=language):
            keyboard = InlineKeyboardBuilder()
            percent = 100 if i18n.default_locale == language else stats.percent_translated
            text += _(
                "\nThe language is {percent}% translated.",
                locale=language,
            ).format(percent=percent)
            if percent > 99:
                text += _(
                    "\nIn case you find any errors, please file a issue in the "
                    "GitHub Repository.",
                    locale=language,
                )
                keyboard.button(
                    text=_("🐞 Open GitHub", locale=language),
                    url=self.github_url,
                )
            else:
                text += _(
                    "\nPlease help us translate this language by completing it on "
                    "the Crowdin website.",
                    locale=language,
                )
                keyboard.button(
                    text=_("🌍 Open Crowdin", locale=language),
                    url=self.crowdin_url,
                )

        return text, keyboard

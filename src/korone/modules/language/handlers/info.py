# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from typing import ClassVar

from babel.support import LazyProxy
from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client, filters
from hydrogram.types import CallbackQuery, InlineKeyboardButton, Message

from korone.database.impl import SQLite3Connection
from korone.decorators import on_callback_query, on_message
from korone.handlers.callback_query_handler import CallbackQueryHandler
from korone.handlers.message_handler import MessageHandler
from korone.modules.language.manager import ChatLanguageManager
from korone.modules.manager import Table
from korone.utils.i18n import I18nNew, get_i18n
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as __

LANG_CMDS: list[str] = ["lang", "language", "locale", "setlang"]


class LanguageInfoBase(MessageHandler):
    button_text: ClassVar[LazyProxy]

    async def get_info_text_and_buttons(
        self, i18n_new: I18nNew
    ) -> tuple[str, InlineKeyboardBuilder]:
        text = _("<b>Chat language:</b> {language}\n").format(
            language=i18n_new.current_locale_display
        )
        if i18n_new.current_locale != i18n_new.default_locale:
            if stats := i18n_new.get_locale_stats(i18n_new.current_locale):
                text += _("\n<b>Language Info:</b>\n")
                text += _("Translated: {translated}\n").format(translated=stats.translated)
                text += _("Untranslated: {untranslated}\n").format(untranslated=stats.untranslated)
                text += _("Needs review: {fuzzy}\n").format(fuzzy=stats.fuzzy)
                text += _("Percentage translated: {percent}\n").format(
                    percent=stats.percent_translated
                )
        else:
            text += _("This is the bot's native language. So it is 100% translated.")

        keyboard = InlineKeyboardBuilder()
        keyboard.button(text=self.button_text, callback_data="selectlanguage")

        return text, keyboard  # type: ignore

    @on_message(filters.command("language"))
    async def handle(self, client: Client, message: Message):
        text, button = await self.get_info_text_and_buttons(get_i18n())
        await message.reply_text(text, reply_markup=button.as_markup())


class LanguagePrivateInfo(LanguageInfoBase):
    @property
    def button_text(self) -> LazyProxy:
        return __("👤 Change your language")

    @staticmethod
    async def group_locale_display(i18n_new: I18nNew, chat_id: int) -> str:
        async with SQLite3Connection() as conn:
            db = ChatLanguageManager(conn, Table.GROUPS)
            chat_lang = await db.get_chat_language(chat_id)

        return i18n_new.locale_display(i18n_new.babel(chat_lang.language))

    handle = on_message(filters.command(LANG_CMDS) & filters.private)(LanguageInfoBase.handle)


class LanguageGroupInfo(LanguageInfoBase):
    @property
    def button_text(self) -> LazyProxy:
        return __("🌍 Change group language")

    handle = on_message(filters.command(LANG_CMDS) & filters.group)(LanguageInfoBase.handle)


class LanguageInfoCallback(CallbackQueryHandler):
    @on_callback_query(filters.regex(r"^languagemenu$"))
    async def handle(self, client: Client, callback: CallbackQuery):
        text, keyboard = await LanguagePrivateInfo().get_info_text_and_buttons(get_i18n())

        keyboard.row(InlineKeyboardButton(text=_("⬅️ Back"), callback_data="startmenu"))
        await callback.message.edit_text(text, reply_markup=keyboard.as_markup())  # type: ignore

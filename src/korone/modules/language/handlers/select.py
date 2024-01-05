# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from hairydogm.i18n import gettext as _
from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client, filters
from hydrogram.enums import ChatType
from hydrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from korone import i18n
from korone.decorators import on_callback_query, on_message
from korone.handlers.callback_query_handler import CallbackQueryHandler
from korone.handlers.message_handler import MessageHandler
from korone.utils.filters import is_admin


class SelectLanguage(MessageHandler):
    @staticmethod
    def build_keyboard(chat_type: ChatType) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardBuilder()

        for language in (*i18n.available_locales, i18n.default_locale):
            keyboard.button(text=language, callback_data=f"setlang:{language}")

        keyboard.adjust(2)
        if chat_type in (ChatType.GROUP, ChatType.SUPERGROUP):
            keyboard.row(InlineKeyboardButton(text=_("❌ Cancel"), callback_data="cancellanguage"))

        if chat_type == ChatType.PRIVATE:
            keyboard.row(InlineKeyboardButton(text=_("⬅️ Back"), callback_data="startmenu"))

        return keyboard.as_markup()  # type: ignore

    @staticmethod
    def build_text() -> str:
        return _("Please select the language you want to use for the chat.")

    @on_message(filters.command("languages") & is_admin)
    async def handle(self, client: Client, message: Message):
        await message.reply_text(
            self.build_text(),
            reply_markup=self.build_keyboard(message.chat.type),
        )


class SelectLanguageCallback(CallbackQueryHandler):
    @on_callback_query(filters.regex(r"^selectlanguage$"))
    async def handle(self, client: Client, callback: CallbackQuery):
        text = SelectLanguage.build_text()
        keyboard = SelectLanguage.build_keyboard(callback.message.chat.type)

        await callback.message.edit_text(text, reply_markup=keyboard)

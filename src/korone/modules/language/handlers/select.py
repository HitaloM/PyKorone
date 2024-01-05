# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from hairydogm.i18n import gettext as _
from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client, filters
from hydrogram.types import InlineKeyboardButton, Message
from korone import i18n
from korone.decorators import on_message
from korone.handlers.message_handler import MessageHandler


class SelectLanguage(MessageHandler):
    @staticmethod
    def build_keyboard() -> InlineKeyboardButton:
        keyboard = InlineKeyboardBuilder()

        for language in (*i18n.available_locales, i18n.default_locale):
            keyboard.button(text=language, callback_data=f"setlang:{language}")

        keyboard.adjust(2)
        keyboard.row(InlineKeyboardButton(text=_("❌ Cancel"), callback_data="cancellanguage"))

        return keyboard.as_markup()  # type: ignore

    @on_message(filters.command("languages"))
    async def handle(self, client: Client, message: Message):
        await message.reply_text(
            _("Please select the language you want to use for the chat."),
            reply_markup=self.build_keyboard(),
        )

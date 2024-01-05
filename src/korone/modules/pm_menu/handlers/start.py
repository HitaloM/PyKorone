# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from hairydogm.i18n import gettext as _
from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client, filters
from hydrogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from korone.decorators import on_callback_query, on_message
from korone.handlers.callback_query_handler import CallbackQueryHandler
from korone.handlers.message_handler import MessageHandler


class Start(MessageHandler):
    @staticmethod
    def build_keyboard() -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text=_("Help"), callback_data="helpmenu")
        keyboard.button(text=_("Language"), callback_data="selectlanguage")
        keyboard.adjust(2)
        return keyboard.as_markup()  # type: ignore

    @staticmethod
    def build_text() -> str:
        return _("Hello, I'm Korone!")

    @on_message(filters.command("start"))
    async def handle(self, client: Client, message: Message) -> None:
        await message.reply_text(
            text=self.build_text(),
            reply_markup=self.build_keyboard(),
        )


class StartCallback(CallbackQueryHandler):
    @on_callback_query(filters.regex(r"^startmenu$"))
    async def handle(self, client: Client, callback: CallbackQuery) -> None:
        text = Start.build_text()
        keyboard = Start.build_keyboard()

        await callback.message.edit_text(text, reply_markup=keyboard)

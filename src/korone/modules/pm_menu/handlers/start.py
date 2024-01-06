# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from babel import Locale
from flag import flag
from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client, filters
from hydrogram.enums import ChatType
from hydrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from korone.decorators import on_callback_query, on_message
from korone.handlers.callback_query_handler import CallbackQueryHandler
from korone.handlers.message_handler import MessageHandler
from korone.utils.i18n import get_i18n
from korone.utils.i18n import gettext as _


class BaseHandler:
    @staticmethod
    def build_keyboard(current_lang: str) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardBuilder()
        locale = Locale.parse(current_lang)

        keyboard.button(text=_("ℹ️ About"), callback_data="aboutmenu")  # noqa: RUF001
        keyboard.button(
            text=_("{lang_flag} Language").format(lang_flag=flag(locale.territory or "US")),
            callback_data="languagemenu",
        )
        keyboard.row(InlineKeyboardButton(text=_("👮‍♂️ Help"), callback_data="helpmenu"))
        keyboard.adjust(2)
        return keyboard.as_markup()  # type: ignore

    @staticmethod
    def build_text() -> str:
        return _("Hello, I'm PyKorone! An all-in-one bot.")


class Start(MessageHandler, BaseHandler):
    @on_message(filters.command("start"))
    async def handle(self, client: Client, message: Message) -> None:
        text = self.build_text()
        keyboard = None
        if message.chat.type == ChatType.PRIVATE:
            keyboard = self.build_keyboard(get_i18n().current_locale)

        await message.reply(text, reply_markup=keyboard)


class StartCallback(CallbackQueryHandler, BaseHandler):
    @on_callback_query(filters.regex(r"^startmenu$"))
    async def handle(self, client: Client, callback: CallbackQuery) -> None:
        text = self.build_text()
        keyboard = self.build_keyboard(get_i18n().current_locale)

        await callback.message.edit_text(text, reply_markup=keyboard)

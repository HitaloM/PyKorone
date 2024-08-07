# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from contextlib import suppress

from babel import Locale
from flag import flag
from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.enums import ChatType
from hydrogram.errors import MessageNotModified
from hydrogram.types import CallbackQuery, InlineKeyboardMarkup, Message
from magic_filter import F

from korone.decorators import router
from korone.filters import Command
from korone.handlers.abstract import CallbackQueryHandler, MessageHandler
from korone.modules.pm_menu.callback_data import LangMenuCallback, PMMenuCallback
from korone.utils.i18n import get_i18n
from korone.utils.i18n import gettext as _


class BaseHandler:
    @staticmethod
    def build_keyboard(current_lang: str) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardBuilder()
        locale = Locale.parse(current_lang)

        keyboard.button(text=_("ℹ️ About"), callback_data=PMMenuCallback(menu="about"))
        keyboard.button(
            text=_("{lang_flag} Language").format(lang_flag=flag(locale.territory or "US")),
            callback_data=LangMenuCallback(menu="language"),
        )
        keyboard.button(text=_("👮‍♂️ Help"), callback_data=PMMenuCallback(menu="help"))

        keyboard.adjust(2)
        return keyboard.as_markup()

    @staticmethod
    def build_text() -> str:
        return _(
            "Hi, I'm Korone! An all-in-one bot. I can help you with lots "
            "of things. Just click on the buttons below to get started."
        )


class Start(MessageHandler, BaseHandler):
    @router.message(Command("start"))
    async def handle(self, client: Client, message: Message) -> None:
        text = self.build_text()

        if message.chat.type != ChatType.PRIVATE:
            await message.reply(text)
            return

        keyboard = self.build_keyboard(get_i18n().current_locale)
        await message.reply(text, reply_markup=keyboard)


class StartCallback(CallbackQueryHandler, BaseHandler):
    @router.callback_query(PMMenuCallback.filter(F.menu == "start"))
    async def handle(self, client: Client, callback: CallbackQuery) -> None:
        text = self.build_text()
        keyboard = self.build_keyboard(get_i18n().current_locale)
        with suppress(MessageNotModified):
            await callback.message.edit(text, reply_markup=keyboard)

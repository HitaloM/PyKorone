# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from contextlib import suppress

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.enums import ChatType
from hydrogram.errors import MessageNotModified
from hydrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from magic_filter import F

from korone import constants
from korone.decorators import router
from korone.filters import Command
from korone.handlers.abstract import CallbackQueryHandler, MessageHandler
from korone.modules.pm_menu.callback_data import PMMenuCallback
from korone.utils.i18n import gettext as _


class HelpBase:
    @staticmethod
    def build_keyboard(message: Message) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text=_("Documentation"), url=constants.DOCS_URL)

        if message.chat.type == ChatType.PRIVATE:
            keyboard.row(
                InlineKeyboardButton(
                    text=_("⬅️ Back"), callback_data=PMMenuCallback(menu="start").pack()
                )
            )

        return keyboard.as_markup()

    @staticmethod
    def build_text() -> str:
        return _(
            "You can get help by reading the documentation, where you'll get an overview of the "
            "bot and how to use it to its full potential. Click the button below to start reading."
        )


class HelpCommand(HelpBase, MessageHandler):
    @router.message(Command("help"))
    async def handle(self, client: Client, message: Message) -> None:
        keyboard = self.build_keyboard(message)
        await message.reply(text=self.build_text(), reply_markup=keyboard)


class HelpCallback(HelpBase, CallbackQueryHandler):
    @router.callback_query(PMMenuCallback.filter(F.menu == "help"))
    async def handle(self, client: Client, callback: CallbackQuery) -> None:
        keyboard = self.build_keyboard(message=callback.message)
        with suppress(MessageNotModified):
            await callback.message.edit(text=self.build_text(), reply_markup=keyboard)

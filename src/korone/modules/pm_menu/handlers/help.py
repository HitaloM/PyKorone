# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.enums import ChatType
from hydrogram.types import (
    CallbackQuery,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Message,
    WebAppInfo,
)
from magic_filter import F

from korone.decorators import router
from korone.filters import Command
from korone.handlers.abstract import CallbackQueryHandler, MessageHandler
from korone.modules.pm_menu.callback_data import PMMenuCallback
from korone.utils.i18n import gettext as _


class HelpBase:
    @staticmethod
    def build_keyboard() -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(
            text=_("Documentation"),
            web_app=WebAppInfo(url="https://pykorone.readthedocs.io/"),
        )
        keyboard.row(
            InlineKeyboardButton(
                text=_("⬅️ Back"), callback_data=PMMenuCallback(menu="start").pack()
            )
        )
        return keyboard.as_markup()

    @staticmethod
    def build_text() -> str:
        return _(
            "Read the documentation, it will give you an introduction to how the bot "
            "works and how to use each of the commands available. You can go to Modules "
            "section to see the list of available commands.\n\n"
            "Start reading by clicking the button below."
        )


class HelpCommand(HelpBase, MessageHandler):
    @router.message(Command("help"))
    async def handle(self, client: Client, message: Message) -> None:
        if message.chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
            bot_username = client.me.username  # type: ignore
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text=_("👮‍♂️ Help"), url=f"https://t.me/{bot_username}?start=start")
            await message.reply(
                _("Message me in PM to get help."), reply_markup=keyboard.as_markup()
            )
            return

        keyboard = self.build_keyboard()
        await message.reply(text=self.build_text(), reply_markup=keyboard)


class HelpCallback(HelpBase, CallbackQueryHandler):
    @router.callback_query(PMMenuCallback.filter(F.menu == "help"))
    async def handle(self, client: Client, callback: CallbackQuery) -> None:
        keyboard = self.build_keyboard()
        await callback.message.edit(text=self.build_text(), reply_markup=keyboard)

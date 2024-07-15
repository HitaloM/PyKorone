# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.enums import ChatType
from hydrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from korone import constants
from korone.decorators import router
from korone.filters import Command
from korone.handlers.abstract import MessageHandler
from korone.modules.pm_menu.callback_data import PMMenuCallback
from korone.utils.i18n import gettext as _


class PrivacyBaseHandler:
    @staticmethod
    def build_keyboard(message: Message) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(
            text=_("Documentation"),
            url=f"{constants.DOCS_URL}/en/latest/privacy.html",
        )

        if message.chat.type == ChatType.PRIVATE:
            keyboard.row(
                InlineKeyboardButton(
                    text=_("🔙 Back"), callback_data=PMMenuCallback(menu="start").pack()
                )
            )

        return keyboard.as_markup()

    @staticmethod
    def build_text() -> str:
        return _(
            "The privacy policy is available for review in the documentation. "
            "Click the button below to start reading."
        )


class PrivacyPolicy(PrivacyBaseHandler, MessageHandler):
    @router.message(Command("privacy"))
    async def handle(self, client: Client, message: Message) -> None:
        text = self.build_text()
        keyboard = self.build_keyboard(message)
        await message.reply(text, reply_markup=keyboard)

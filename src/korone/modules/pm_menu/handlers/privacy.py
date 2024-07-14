# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from contextlib import suppress

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.errors import MessageNotModified
from hydrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from magic_filter import F

from korone import constants
from korone.decorators import router
from korone.filters import Command
from korone.filters.chat import IsPrivateChat
from korone.handlers.abstract import CallbackQueryHandler, MessageHandler
from korone.modules.pm_menu.callback_data import PMMenuCallback
from korone.utils.i18n import gettext as _


class PrivacyBaseHandler:
    @staticmethod
    def build_keyboard() -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(
            text=_("What Information We Collect"),
            url=f"{constants.DOCS_URL}/en/latest/privacy.html",
        )
        keyboard.adjust(1)
        keyboard.row(
            InlineKeyboardButton(
                text=_("🔙 Back"), callback_data=PMMenuCallback(menu="start").pack()
            )
        )
        return keyboard.as_markup()

    @staticmethod
    def build_text() -> str:
        return _(
            "<b>Korone Privacy Policy</b>\n\n"
            "This bot is designed to prioritize and protect user privacy to the best of its "
            "ability.\n\nThe bot only collects and uses the data necessary for the proper "
            "functioning of its commands that are listed in the {modules} section in the "
            "documentation.\n\nPlease note that our privacy policy may be subject to changes "
            "and updates."
        ).format(
            modules=f"<a href='{constants.DOCS_URL}/en/latest/modules/index.html'>Modules</a>",
        )


class PrivacyPolicy(PrivacyBaseHandler, MessageHandler):
    @router.message(Command("privacy") & IsPrivateChat)
    async def handle(self, client: Client, message: Message) -> None:
        text = self.build_text()
        keyboard = self.build_keyboard()
        await message.reply(text, reply_markup=keyboard)


class PrivacyPolicyCallback(PrivacyBaseHandler, CallbackQueryHandler):
    @router.callback_query(PMMenuCallback.filter(F.menu == "privacy"))
    async def handle(self, client: Client, callback: CallbackQuery) -> None:
        text = self.build_text()
        keyboard = self.build_keyboard()
        with suppress(MessageNotModified):
            await callback.message.edit(text, reply_markup=keyboard)

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.types import CallbackQuery, InlineKeyboardButton, Message, WebAppInfo
from magic_filter import F

from korone.decorators import router
from korone.filters import Command
from korone.filters.chat import IsPrivateChat
from korone.handlers.abstract import CallbackQueryHandler, MessageHandler
from korone.modules.pm_menu.callback_data import PMMenuCallback
from korone.utils.i18n import gettext as _


class PrivacyBaseHandler:
    @staticmethod
    def get_privacy_message_and_keyboard():
        text = _(
            "<b>Korone Privacy Policy</b>\n\n"
            "This bot is designed to prioritize and protect user privacy to the best of its "
            "ability.\n\nThe bot only collects and uses the data necessary for the proper "
            "functioning of its commands that are listed in the /help section.\n\nPlease note "
            "that our privacy policy may be subject to changes and updates."
        )
        keyboard = InlineKeyboardBuilder()
        keyboard.button(
            text=_("What Information We Collect"),
            web_app=WebAppInfo(url="https://pykorone.readthedocs.io/en/latest/privacy.html"),
        )
        keyboard.adjust(1)
        keyboard.row(
            InlineKeyboardButton(
                text=_("🔙 Back"), callback_data=PMMenuCallback(menu="start").pack()
            )
        )
        return text, keyboard.as_markup()


class PrivacyPolicy(PrivacyBaseHandler, MessageHandler):
    @staticmethod
    @router.message(Command("privacy") & IsPrivateChat)
    async def handle(client: Client, message: Message):
        text, keyboard = PrivacyBaseHandler.get_privacy_message_and_keyboard()
        await message.reply(text, reply_markup=keyboard)


class PrivacyPolicyCallback(PrivacyBaseHandler, CallbackQueryHandler):
    @staticmethod
    @router.callback_query(PMMenuCallback.filter(F.menu == "privacy"))
    async def handle(client: Client, callback: CallbackQuery):
        text, keyboard = PrivacyBaseHandler.get_privacy_message_and_keyboard()
        await callback.message.edit(text, reply_markup=keyboard)

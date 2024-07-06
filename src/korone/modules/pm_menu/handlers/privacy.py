# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.types import CallbackQuery, InlineKeyboardButton, Message
from magic_filter import F

from korone.decorators import router
from korone.filters import Command
from korone.filters.chat import IsPrivateChat
from korone.handlers.abstract import CallbackQueryHandler, MessageHandler
from korone.modules.pm_menu.callback_data import PMMenuCallback, PrivacyCallback
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
            callback_data=PrivacyCallback(section="policy"),
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


class PrivacySection(CallbackQueryHandler):
    @staticmethod
    @router.callback_query(PrivacyCallback.filter(F.section == "policy"))
    async def handle(client: Client, callback: CallbackQuery):
        if not callback.data:
            return

        text = _(
            "<b>Information We Collect</b>\n"
            "The bot collects the following information:\n"
            "- <b>Telegram Details:</b> User ID, first name, last name, and username.\n"
            "- <b>Group Information:</b> ID, title, username, and type.\n"
            "- <b>Bot Settings/Configurations:</b> Any settings or configurations you've "
            "applied, such as your LastFM username for related commands.\n\n"
            "<b>How and Why We Collect Your Information</b>\n"
            "The information we process is obtained directly from you when you interact "
            "with the bot in the following ways:\n"
            "- <b>Direct Messaging:</b> When you message the bot privately or initiate a "
            "conversation using the /start command.\n"
            "- <b>Group Interactions:</b> When you interact with the bot in a group chat.\n"
            "The information collected is used to provide you with the services you request "
            "and to improve the bot's functionality.\n\n"
            "<b>Note:</b> All these informations is publicly available on Telegram, and we "
            "do not know your 'real' identity."
        )

        keyboard = InlineKeyboardBuilder()
        keyboard.row(
            InlineKeyboardButton(
                text=_("🔙 Back"), callback_data=PMMenuCallback(menu="privacy").pack()
            )
        )
        await callback.message.edit(text, reply_markup=keyboard.as_markup())

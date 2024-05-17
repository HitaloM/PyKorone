# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.enums import ChatType
from hydrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from magic_filter import F

from korone import commit_count, commit_hash, constants
from korone.decorators import router
from korone.handlers import CallbackQueryHandler, MessageHandler
from korone.modules.pm_menu.callback_data import PMMenuCallback
from korone.modules.utils.filters import Command
from korone.utils.i18n import gettext as _


class BaseHandler:
    github_url: str = constants.GITHUB_URL
    telegram_url: str = constants.TELEGRAM_URL
    license_url: str = "https://github.com/HitaloM/PyKorone/blob/main/LICENSE"
    hydrogram_url: str = "https://github.com/hydrogram/hydrogram"

    def build_keyboard(self, message: Message) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text=_("📦 GitHub"), url=self.github_url)
        keyboard.button(text=_("📚 Channel"), url=self.telegram_url)
        keyboard.adjust(2)

        if message.chat.type == ChatType.PRIVATE:
            keyboard.row(
                InlineKeyboardButton(
                    text=_("⬅️ Back"), callback_data=PMMenuCallback(menu="start").pack()
                )
            )

        return keyboard.as_markup()

    def build_text(self) -> str:
        hydrogram_link = f"<a href='{self.hydrogram_url}'>Hydrogram</a>"
        license_link = f"<a href='{self.license_url}'>BSD 3-Clause</a>"
        version = (
            f"r{commit_count} (<a href='{self.github_url}/commit/{commit_hash}'>{commit_hash}</a>)"
        )

        text = _(
            "PyKorone is a comprehensive and cutting-edge Telegram bot that offers a wide range "
            "of features to enhance your Telegram experience. It is designed to be versatile, "
            "adaptable, and highly efficient.\n\nBuilt using Python, PyKorone is based on the "
            "{hydrogram} framework, which uses the Telegram MTProto API.\n\nPyKorone is an "
            "open source project licensed under the {license_link} License. The source code "
            "can be found on GitHub.\n\n"
            "PyKororne version: {version}"
        )

        return text.format(hydrogram=hydrogram_link, license_link=license_link, version=version)


class About(MessageHandler, BaseHandler):
    @router.message(Command("about"))
    async def handle(self, client: Client, message: Message) -> None:
        text = self.build_text()
        keyboard = self.build_keyboard(message)

        await message.reply(text, reply_markup=keyboard, disable_web_page_preview=True)


class AboutCallback(CallbackQueryHandler, BaseHandler):
    @router.callback_query(PMMenuCallback.filter(F.menu == "about"))
    async def handle(self, client: Client, callback: CallbackQuery) -> None:
        text = self.build_text()
        keyboard = self.build_keyboard(callback.message)

        await callback.message.edit_text(
            text, reply_markup=keyboard, disable_web_page_preview=True
        )

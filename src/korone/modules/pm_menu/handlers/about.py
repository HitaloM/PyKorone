# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client, filters
from hydrogram.enums import ChatType
from hydrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from korone.decorators import on_callback_query, on_message
from korone.handlers.callback_query_handler import CallbackQueryHandler
from korone.handlers.message_handler import MessageHandler
from korone.utils.i18n import gettext as _


class BaseHandler:
    @staticmethod
    def build_keyboard(message: Message) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(text=_("📦 GitHub"), url="https://github.com/HitaloM/PyKorone")
        keyboard.button(text=_("📚 Channel"), url="https://t.me/HitaloProjects")
        keyboard.adjust(2)

        if message.chat.type == ChatType.PRIVATE:
            keyboard.row(InlineKeyboardButton(text=_("⬅️ Back"), callback_data="startmenu"))

        return keyboard.as_markup()  # type: ignore

    @staticmethod
    def build_text() -> str:
        return _(
            "PyKorone is a comprehensive, cutting-edge Telegram Bot that provides a variety of "
            "features to enhance your Telegram experience. It is designed to be versatile and "
            "adaptable, catering to a wide range of user needs. The bot is built using Python "
            "and is designed to be highly efficient and reliable.\n\n"
            "PyKorone uses {hydrogram}, a framework for the Telegram MTProto API, as its base.\n\n"
            "PyKorone is open source and is licensed under the {license_link} License. "
            "The source code is available on GitHub."
        ).format(
            hydrogram="<a href='https://github.com/hydrogram/hydrogram'>Hydrogram</a>",
            license_link="<a href='https://github.com/HitaloM/PyKorone/blob/main/LICENSE'>"
            "BSD 3-Clause</a>",
        )


class About(MessageHandler, BaseHandler):
    @on_message(filters.command("about"))
    async def handle(self, client: Client, message: Message) -> None:
        text = self.build_text()
        keyboard = self.build_keyboard(message)

        await message.reply(text, reply_markup=keyboard, disable_web_page_preview=True)


class AboutCallback(CallbackQueryHandler, BaseHandler):
    @on_callback_query(filters.regex(r"^aboutmenu$"))
    async def handle(self, client: Client, callback: CallbackQuery) -> None:
        text = self.build_text()
        keyboard = self.build_keyboard(callback.message)

        await callback.message.edit_text(
            text, reply_markup=keyboard, disable_web_page_preview=True
        )

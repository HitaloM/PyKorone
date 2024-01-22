# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client, filters
from hydrogram.enums import ChatMemberStatus, ChatType
from hydrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from magic_filter import F

from korone import i18n
from korone.client import Korone
from korone.handlers.callback_query_handler import CallbackQueryHandler
from korone.handlers.message_handler import MessageHandler
from korone.modules.language.callback_data import LangMenuCallback, SetLangCallback
from korone.modules.utils.filters import is_admin
from korone.utils.i18n import gettext as _


class SelectLanguageBase:
    @staticmethod
    def build_keyboard(chat_type: ChatType) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardBuilder()

        for language in (*i18n.available_locales, i18n.default_locale):
            locale = i18n.babel(language)
            keyboard.button(
                text=i18n.locale_display(locale), callback_data=SetLangCallback(lang=language)
            )

        keyboard.adjust(2)
        if chat_type in (ChatType.GROUP, ChatType.SUPERGROUP):
            keyboard.row(
                InlineKeyboardButton(
                    text=_("❌ Cancel"), callback_data=LangMenuCallback(menu="cancel").pack()
                )
            )

        if chat_type == ChatType.PRIVATE:
            keyboard.row(
                InlineKeyboardButton(
                    text=_("⬅️ Back"), callback_data=LangMenuCallback(menu="language").pack()
                )
            )

        return keyboard.as_markup()  # type: ignore

    @staticmethod
    def build_text() -> str:
        return _("Please select the language you want to use for the chat.")

    async def send_message(self, message: Message):
        await message.reply_text(
            self.build_text(),
            reply_markup=self.build_keyboard(message.chat.type),
        )

    async def edit_message(self, callback: CallbackQuery):
        await callback.edit_message_text(
            self.build_text(),
            reply_markup=self.build_keyboard(callback.message.chat.type),
        )


class SelectLanguage(MessageHandler, SelectLanguageBase):
    @Korone.on_message(filters.command("languages") & is_admin)
    async def handle(self, client: Client, message: Message):
        await self.send_message(message)


class SelectLanguageCallback(CallbackQueryHandler, SelectLanguageBase):
    @Korone.on_callback_query(LangMenuCallback.filter(F.menu == "languages") & is_admin)
    async def handle(self, client: Client, callback: CallbackQuery):
        if callback.message.chat.type != ChatType.PRIVATE:
            user = await client.get_chat_member(callback.message.chat.id, callback.from_user.id)
            if user.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
                await callback.answer(_("This action can only be performed by administrators."))

        await self.edit_message(callback)

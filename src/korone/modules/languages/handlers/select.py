# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.enums import ChatType
from hydrogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from magic_filter import F

from korone.decorators import router
from korone.filters import Command, IsAdmin
from korone.modules.languages.callback_data import LangMenu, LangMenuCallback, SetLangCallback
from korone.utils.i18n import I18nNew, get_i18n
from korone.utils.i18n import gettext as _


def build_text_and_keyboard(
    i18n: I18nNew, chat_type: ChatType
) -> tuple[str, InlineKeyboardMarkup]:
    keyboard = InlineKeyboardBuilder()

    for language in (*i18n.available_locales, i18n.default_locale):
        locale = i18n.babel(language)
        keyboard.button(
            text=i18n.locale_display(locale), callback_data=SetLangCallback(lang=language)
        )

    keyboard.adjust(2)

    if chat_type in {ChatType.GROUP, ChatType.SUPERGROUP}:
        keyboard.row(
            InlineKeyboardButton(
                text=_("❌ Cancel"), callback_data=LangMenuCallback(menu=LangMenu.Cancel).pack()
            )
        )

    if chat_type == ChatType.PRIVATE:
        keyboard.row(
            InlineKeyboardButton(
                text=_("⬅️ Back"), callback_data=LangMenuCallback(menu=LangMenu.Languages).pack()
            )
        )

    text = _("Please select the language you want to use for the chat.")
    return text, keyboard.as_markup()


@router.message(Command("languages") & IsAdmin)
@router.callback_query(LangMenuCallback.filter(F.menu == LangMenu.Languages) & IsAdmin)
async def languages_command(client: Client, update: Message | CallbackQuery) -> None:
    text, keyboard = build_text_and_keyboard(
        get_i18n(), update.chat.type if isinstance(update, Message) else update.message.chat.type
    )

    if isinstance(update, Message):
        await update.reply(text, reply_markup=keyboard)
    else:
        await update.edit_message_text(text, reply_markup=keyboard)

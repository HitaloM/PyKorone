# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from contextlib import suppress

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.enums import ChatType
from hydrogram.errors import MessageNotModified
from hydrogram.types import CallbackQuery, InlineKeyboardButton, Message
from magic_filter import F

from korone.decorators import router
from korone.filters import Command, UserIsAdmin
from korone.modules.languages.callback_data import LangMenu, LangMenuCallback, SetLangCallback
from korone.utils.i18n import get_i18n
from korone.utils.i18n import gettext as _


@router.message(Command("languages") & UserIsAdmin)
@router.callback_query(LangMenuCallback.filter(F.menu == LangMenu.Languages) & UserIsAdmin)
async def handle_languages(client: Client, update: Message | CallbackQuery) -> None:
    i18n = get_i18n()
    chat_type = update.chat.type if isinstance(update, Message) else update.message.chat.type
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
                text=_("⬅️ Back"), callback_data=LangMenuCallback(menu=LangMenu.Language).pack()
            )
        )

    text = _("Please select the language you want to use for the chat.")

    if isinstance(update, Message):
        await update.reply(text, reply_markup=keyboard.as_markup())
        return

    with suppress(MessageNotModified):
        await update.edit_message_text(text, reply_markup=keyboard.as_markup())

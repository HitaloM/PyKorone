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
from korone.filters import Command
from korone.modules.languages.callback_data import LangMenu, LangMenuCallback
from korone.modules.pm_menu.callback_data import PMMenu, PMMenuCallback
from korone.utils.i18n import I18nNew, get_i18n
from korone.utils.i18n import gettext as _


@router.message(Command(commands=["language", "lang", "locale", "setlang"]))
@router.callback_query(LangMenuCallback.filter(F.menu == LangMenu.Language))
async def handle_language(client: Client, update: Message | CallbackQuery) -> None:
    is_message = isinstance(update, Message)
    chat_type = update.chat.type if is_message else update.message.chat.type

    i18n = get_i18n()
    text = build_language_info_text(i18n)

    keyboard = build_keyboard(chat_type)

    if is_message:
        await update.reply(text, reply_markup=keyboard.as_markup())
        return

    with suppress(MessageNotModified):
        await update.message.edit(text, reply_markup=keyboard.as_markup())


def build_language_info_text(i18n: I18nNew) -> str:
    text = _("<b>Chat language:</b> {language}\n").format(language=i18n.current_locale_display)

    if i18n.current_locale == i18n.default_locale:
        text += _("This is the bot's native language. So it is 100% translated.")
    elif stats := i18n.get_locale_stats(i18n.current_locale):
        text += _("\n<b>Language Information:</b>\n")
        text += _("Translated strings: <code>{translated}</code>\n").format(
            translated=stats.translated
        )
        text += _("Untranslated strings: <code>{untranslated}</code>\n").format(
            untranslated=stats.untranslated
        )
        text += _("Strings requiring review: <code>{fuzzy}</code>\n").format(fuzzy=stats.fuzzy)

    return text


def get_button_text(chat_type: ChatType) -> str:
    return (
        _("👤 Change your language")
        if chat_type == ChatType.PRIVATE
        else _("🌍 Change group language")
    )


def build_keyboard(chat_type: ChatType) -> InlineKeyboardBuilder:
    button_text = get_button_text(chat_type)

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=button_text, callback_data=LangMenuCallback(menu=LangMenu.Languages))
    if chat_type == ChatType.PRIVATE:
        keyboard.row(
            InlineKeyboardButton(
                text=_("⬅️ Back"), callback_data=PMMenuCallback(menu=PMMenu.Start).pack()
            )
        )
    return keyboard

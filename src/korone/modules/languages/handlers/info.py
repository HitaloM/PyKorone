# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

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
async def language_command(client: Client, message: Message):
    button_text = (
        _("👤 Change your language")
        if message.chat.type == ChatType.PRIVATE
        else _("🌍 Change group language")
    )
    text, keyboard = get_info_text_and_buttons(get_i18n(), button_text)

    if message.chat.type == ChatType.PRIVATE:
        keyboard.row(
            InlineKeyboardButton(
                text=_("⬅️ Back"), callback_data=PMMenuCallback(menu=PMMenu.Start).pack()
            )
        )

    await message.reply(text, reply_markup=keyboard.as_markup())


@router.callback_query(LangMenuCallback.filter(F.menu == LangMenu.Language))
async def language_callback(client: Client, callback: CallbackQuery):
    button_text = _("👤 Change your language")
    text, keyboard = get_info_text_and_buttons(get_i18n(), button_text)

    keyboard.row(
        InlineKeyboardButton(
            text=_("⬅️ Back"), callback_data=PMMenuCallback(menu=PMMenu.Start).pack()
        )
    )

    with suppress(MessageNotModified):
        await callback.message.edit(text, reply_markup=keyboard.as_markup())


def get_info_text_and_buttons(
    i18n: I18nNew, button_text: str
) -> tuple[str, InlineKeyboardBuilder]:
    text = _("<b>Chat language:</b> {language}\n").format(language=i18n.current_locale_display)

    if i18n.current_locale != i18n.default_locale:
        text += get_language_info(i18n)
    else:
        text += _("This is the bot's native language. So it is 100% translated.")

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=button_text, callback_data=LangMenuCallback(menu=LangMenu.Languages))

    return text, keyboard


def get_language_info(i18n: I18nNew) -> str:
    stats = i18n.get_locale_stats(i18n.current_locale)
    if not stats:
        return ""

    info = _("\n<b>Language Information:</b>\n")
    info += _("Translated strings: <code>{translated}</code>\n").format(
        translated=stats.translated
    )
    info += _("Untranslated strings: <code>{untranslated}</code>\n").format(
        untranslated=stats.untranslated
    )
    info += _("Strings requiring review: <code>{fuzzy}</code>\n").format(fuzzy=stats.fuzzy)

    return info

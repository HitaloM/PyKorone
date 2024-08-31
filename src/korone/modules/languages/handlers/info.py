# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from contextlib import suppress

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.enums import ChatType
from hydrogram.errors import MessageNotModified
from hydrogram.types import InlineKeyboardButton, Message
from magic_filter import F

from korone.decorators import router
from korone.filters import Command
from korone.modules.languages.callback_data import LangMenu, LangMenuCallback
from korone.modules.pm_menu.callback_data import PMMenu, PMMenuCallback
from korone.utils.i18n import get_i18n
from korone.utils.i18n import gettext as _


@router.message(Command(commands=["language", "lang", "locale", "setlang"]))
@router.callback_query(LangMenuCallback.filter(F.menu == LangMenu.Language))
async def handle_language(client: Client, event):
    is_message = isinstance(event, Message)
    chat_type = event.chat.type if is_message else event.message.chat.type
    button_text = (
        _("👤 Change your language")
        if chat_type == ChatType.PRIVATE
        else _("🌍 Change group language")
    )

    i18n = get_i18n()
    text = _("<b>Chat language:</b> {language}\n").format(language=i18n.current_locale_display)
    if i18n.current_locale != i18n.default_locale:
        stats = i18n.get_locale_stats(i18n.current_locale)
        if stats:
            text += _("\n<b>Language Information:</b>\n")
            text += _("Translated strings: <code>{translated}</code>\n").format(
                translated=stats.translated
            )
            text += _("Untranslated strings: <code>{untranslated}</code>\n").format(
                untranslated=stats.untranslated
            )
            text += _("Strings requiring review: <code>{fuzzy}</code>\n").format(fuzzy=stats.fuzzy)
    else:
        text += _("This is the bot's native language. So it is 100% translated.")

    keyboard = InlineKeyboardBuilder()
    keyboard.button(text=button_text, callback_data=LangMenuCallback(menu=LangMenu.Languages))
    if chat_type == ChatType.PRIVATE:
        keyboard.row(
            InlineKeyboardButton(
                text=_("⬅️ Back"), callback_data=PMMenuCallback(menu=PMMenu.Start).pack()
            )
        )

    if is_message:
        await event.reply(text, reply_markup=keyboard.as_markup())
    else:
        with suppress(MessageNotModified):
            await event.message.edit(text, reply_markup=keyboard.as_markup())

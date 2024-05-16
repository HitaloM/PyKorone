# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from typing import ClassVar

from babel.support import LazyProxy
from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client, filters
from hydrogram.enums import ChatType
from hydrogram.types import CallbackQuery, InlineKeyboardButton, Message
from magic_filter import F

from korone.decorators import router
from korone.handlers import CallbackQueryHandler, MessageHandler
from korone.modules.language.callback_data import LangMenuCallback, PMMenuCallback
from korone.modules.utils.filters import Command
from korone.utils.i18n import I18nNew, get_i18n
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as __

LANG_CMDS: list[str] = ["language", "lang", "locale", "setlang"]


class LanguageInfoBase(MessageHandler):
    button_text: ClassVar[LazyProxy]

    async def get_info_text_and_buttons(
        self, i18n_new: I18nNew
    ) -> tuple[str, InlineKeyboardBuilder]:
        text = _("<b>Chat language:</b> {language}\n").format(
            language=i18n_new.current_locale_display
        )

        if i18n_new.current_locale != i18n_new.default_locale:
            stats = i18n_new.get_locale_stats(i18n_new.current_locale)
            if not stats:
                return text, InlineKeyboardBuilder().button(
                    text=self.button_text, callback_data=LangMenuCallback(menu="languages")
                )

            text += _("\n<b>Language Info:</b>\n")
            text += _("Translated: {translated}\n").format(translated=stats.translated)
            text += _("Untranslated: {untranslated}\n").format(untranslated=stats.untranslated)
            text += _("Needs review: {fuzzy}\n").format(fuzzy=stats.fuzzy)
            text += _("Percentage translated: {percent}\n").format(
                percent=stats.percent_translated
            )
        else:
            text += _("This is the bot's native language. So it is 100% translated.")

        keyboard = InlineKeyboardBuilder()
        keyboard.button(text=self.button_text, callback_data=LangMenuCallback(menu="languages"))

        return text, keyboard

    @router.message(Command("language"))
    async def handle(self, client: Client, message: Message):
        text, keyboard = await self.get_info_text_and_buttons(get_i18n())

        if message.chat.type == ChatType.PRIVATE:
            keyboard.row(
                InlineKeyboardButton(
                    text=_("⬅️ Back"), callback_data=PMMenuCallback(menu="start").pack()
                )
            )

        await message.reply_text(text, reply_markup=keyboard.as_markup())


class LanguagePrivateInfo(LanguageInfoBase):
    @property
    def button_text(self) -> LazyProxy:
        return __("👤 Change your language")

    handle = router.message(Command(commands=LANG_CMDS) & filters.private)(LanguageInfoBase.handle)


class LanguageGroupInfo(LanguageInfoBase):
    @property
    def button_text(self) -> LazyProxy:
        return __("🌍 Change group language")

    handle = router.message(Command(commands=LANG_CMDS) & filters.group)(LanguageInfoBase.handle)


class LanguageInfoCallback(CallbackQueryHandler):
    @staticmethod
    @router.callback_query(LangMenuCallback.filter(F.menu == "language"))
    async def handle(client: Client, callback: CallbackQuery):
        text, keyboard = await LanguagePrivateInfo().get_info_text_and_buttons(get_i18n())

        keyboard.row(
            InlineKeyboardButton(
                text=_("⬅️ Back"), callback_data=PMMenuCallback(menu="start").pack()
            )
        )

        await callback.message.edit_text(text, reply_markup=keyboard.as_markup())

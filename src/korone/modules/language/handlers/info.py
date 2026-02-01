from typing import TYPE_CHECKING, cast

from aiogram import flags
from aiogram.types import InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from magic_filter import F
from stfu_tg import Code, KeyValue, Section

from korone.filters.chat_status import ChatTypeFilter
from korone.filters.cmd import CMDFilter
from korone.modules.language.callbacks import LangMenu, LangMenuCallback
from korone.modules.utils_.callbacks import GoToStartCallback
from korone.utils.handlers import KoroneCallbackQueryHandler, KoroneMessageHandler
from korone.utils.i18n import get_i18n
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType

    from korone.utils.i18n import I18nNew


def build_language_info_text(i18n: I18nNew) -> str:
    section = Section(KeyValue(_("Current Language"), i18n.current_locale_display), title=_("Language Settings"))

    if i18n.is_current_locale_default():
        section += _("This is the bot's native language, so it is 100% translated.")
    elif stats := i18n.get_current_locale_stats():
        section += KeyValue(_("Translated strings"), Code(stats.translated))
        section += KeyValue(_("Untranslated strings"), Code(stats.untranslated))
        section += KeyValue(_("Strings requiring review"), Code(stats.fuzzy))

    return str(section)


def build_keyboard(*, is_private: bool, back_to_start: bool = False) -> InlineKeyboardBuilder:
    button_text = _("👤 Change your language") if is_private else _("🌍 Change group language")

    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text=button_text, callback_data=LangMenuCallback(menu=LangMenu.Languages, back_to_start=back_to_start)
    )

    if is_private and back_to_start:
        keyboard.row(InlineKeyboardButton(text=_("⬅️ Back"), callback_data=GoToStartCallback().pack()))

    return keyboard


@flags.help(description=l_("Shows the current language settings."))
class LanguageInfoHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter(["language"]),)

    async def handle(self) -> None:
        is_private = self.event.chat.type == "private"

        i18n = get_i18n()
        text = build_language_info_text(i18n)
        keyboard = build_keyboard(is_private=is_private, back_to_start=False)

        await self.event.reply(text, reply_markup=keyboard.as_markup())


@flags.help(exclude=True)
class LanguageInfoCallbackHandler(KoroneCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (LangMenuCallback.filter(F.menu == LangMenu.Language), ChatTypeFilter("private"))

    async def handle(self) -> None:
        i18n = get_i18n()
        text = build_language_info_text(i18n)

        callback_data = cast("LangMenuCallback", self.callback_data)
        back_to_start = callback_data.back_to_start

        keyboard = build_keyboard(is_private=True, back_to_start=back_to_start)

        message = self.event.message
        if isinstance(message, Message):
            await message.edit_text(text, reply_markup=keyboard.as_markup())

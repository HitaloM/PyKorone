from typing import TYPE_CHECKING, cast

from aiogram import flags
from aiogram.enums import ButtonStyle, ChatType
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from magic_filter import F

from korone.filters.chat_status import PrivateChatFilter
from korone.modules.language.callbacks import LangMenu, LangMenuCallback
from korone.modules.utils_.callbacks import GoToStartCallback
from korone.ui import Code, UIExpression, field, section
from korone.utils.handlers import KoroneCallbackQueryHandler, KoroneMessageHandler
from korone.utils.i18n import get_i18n
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType

    from korone.utils.i18n import I18nNew


def build_language_info_text(i18n: I18nNew) -> UIExpression:
    details: list[UIExpression | str] = [field(_("Current Language"), i18n.current_locale_display)]
    if i18n.is_current_locale_default():
        details.append(_("This is the bot's native language, so it is 100% translated."))
    elif stats := i18n.get_current_locale_stats():
        details.extend((
            field(_("Translated strings"), Code(stats.translated)),
            field(_("Untranslated strings"), Code(stats.untranslated)),
            field(_("Strings requiring review"), Code(stats.fuzzy)),
        ))

    return section(_("Language Settings"), *details)


def build_keyboard(*, is_private: bool, back_to_start: bool = False) -> InlineKeyboardBuilder:
    button_text = _("👤 Change your language") if is_private else _("🌍 Change group language")

    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text=button_text, callback_data=LangMenuCallback(menu=LangMenu.Languages, back_to_start=back_to_start)
    )

    if is_private and back_to_start:
        keyboard.button(text=_("⬅️ Back"), style=ButtonStyle.PRIMARY, callback_data=GoToStartCallback())

    keyboard.adjust(1)

    return keyboard


@flags.help(description=l_("Show current language settings for this chat."))
class LanguageInfoHandler(KoroneMessageHandler):
    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return (Command("language"),)

    async def handle(self) -> None:
        is_private = self.event.chat.type == ChatType.PRIVATE

        i18n = get_i18n()
        text = build_language_info_text(i18n)
        keyboard = build_keyboard(is_private=is_private, back_to_start=False)

        await self.answer(text, reply_markup=keyboard.as_markup())


@flags.help(exclude=True)
class LanguageInfoCallbackHandler(KoroneCallbackQueryHandler):
    @classmethod
    def filters(cls) -> tuple[CallbackType, ...]:
        return (LangMenuCallback.filter(F.menu == LangMenu.Language), PrivateChatFilter())

    async def handle(self) -> None:
        i18n = get_i18n()
        text = build_language_info_text(i18n)

        callback_data = cast("LangMenuCallback", self.callback_data)
        back_to_start = callback_data.back_to_start

        keyboard = build_keyboard(is_private=True, back_to_start=back_to_start)
        await self.edit_text(text, reply_markup=keyboard.as_markup())

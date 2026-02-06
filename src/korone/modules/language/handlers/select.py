from typing import TYPE_CHECKING, cast

from aiogram import flags
from aiogram.enums import ChatType
from aiogram.types import InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from magic_filter import F

from korone.filters.admin_rights import UserRestricting
from korone.filters.chat_status import PrivateChatFilter
from korone.filters.cmd import CMDFilter
from korone.modules.language.callbacks import LangMenu, LangMenuCallback, SetLangCallback
from korone.modules.utils_.callbacks import CancelActionCallback, GoToStartCallback, LanguageButtonCallback
from korone.utils.handlers import KoroneCallbackQueryHandler, KoroneMessageHandler
from korone.utils.i18n import get_i18n
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType

    from korone.utils.i18n import I18nNew


def build_language_selection_keyboard(
    i18n: I18nNew, *, is_private: bool, back_to_start: bool = False
) -> InlineKeyboardBuilder:
    keyboard = InlineKeyboardBuilder()

    all_locales = [i18n.default_locale, *sorted(i18n.available_locales)]
    seen = set()
    unique_locales = []
    for loc in all_locales:
        if loc not in seen:
            seen.add(loc)
            unique_locales.append(loc)

    for language in unique_locales:
        locale = i18n.babels.get(language) or i18n.babel(language)
        keyboard.button(
            text=i18n.locale_display(locale), callback_data=SetLangCallback(lang=language, back_to_start=back_to_start)
        )

    keyboard.adjust(2)

    if not is_private:
        keyboard.row(InlineKeyboardButton(text=_("❌ Cancel"), callback_data=CancelActionCallback().pack()))

    if is_private:
        if back_to_start:
            keyboard.row(InlineKeyboardButton(text=_("⬅️ Back"), callback_data=GoToStartCallback().pack()))
        else:
            keyboard.row(
                InlineKeyboardButton(
                    text=_("⬅️ Back"), callback_data=LangMenuCallback(menu=LangMenu.Language, back_to_start=False).pack()
                )
            )

    return keyboard


@flags.help(description=l_("Shows the available languages for selection."))
class LanguageSelectHandler(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter("languages"), UserRestricting(admin=True))

    async def handle(self) -> None:
        is_private = self.event.chat.type == ChatType.PRIVATE

        i18n = get_i18n()
        text = _("Please select the language you want to use for the chat.")
        keyboard = build_language_selection_keyboard(i18n, is_private=is_private, back_to_start=False)

        await self.event.reply(text, reply_markup=keyboard.as_markup())


@flags.help(exclude=True)
class LanguageSelectCallbackHandler(KoroneCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (LangMenuCallback.filter(F.menu == LangMenu.Languages), UserRestricting(admin=True))

    async def handle(self) -> None:
        message = self.event.message
        if not isinstance(message, Message) or not message.chat:
            return

        is_private = message.chat.type == ChatType.PRIVATE

        callback_data = cast("LangMenuCallback", self.callback_data)
        back_to_start = callback_data.back_to_start

        i18n = get_i18n()
        text = _("Please select the language you want to use for the chat.")
        keyboard = build_language_selection_keyboard(i18n, is_private=is_private, back_to_start=back_to_start)

        await message.edit_text(text, reply_markup=keyboard.as_markup())


@flags.help(exclude=True)
class LanguageSelectPMHandler(KoroneCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (LanguageButtonCallback.filter(), PrivateChatFilter())

    async def handle(self) -> None:
        i18n = get_i18n()
        text = _("Please select the language you want to use for the chat.")
        keyboard = build_language_selection_keyboard(i18n, is_private=True, back_to_start=True)

        message = self.event.message
        if isinstance(message, Message):
            await message.edit_text(text, reply_markup=keyboard.as_markup())

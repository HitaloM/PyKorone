from typing import Any

from aiogram import Router, flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.utils.handlers import SophieCallbackQueryHandler, SophieMessageHandler
from sophie_bot.utils.i18n import get_i18n, gettext as _, lazy_gettext as l_

router = Router(name="language")


class SelectLangCb(CallbackData, prefix="set_lang"):
    code: str


@flags.help(description=l_("Change the language of the bot in the chat."))
class LanguageHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter("lang"), UserRestricting(admin=True))

    async def handle(self) -> Any:
        message: Message = self.event
        i18n = get_i18n()

        # Get current chat language from connection
        current_lang_code = self.connection.db_model.language_code if self.connection.db_model else i18n.default_locale

        text = _("Select the language you want to use in this chat.")
        text += "\n\n"

        buttons = []
        for code in i18n.available_locales:
            locale = i18n.babels.get(code)
            display_name = i18n.locale_display(locale) if locale else code

            # Add translation stats if available
            stats = i18n.get_locale_stats(code)
            if stats and stats.percent_translated() < 100:
                display_name += f" ({stats.percent_translated()}%)"

            # Mark current language
            if code == current_lang_code:
                display_name = f"✅ {display_name}"

            buttons.append(InlineKeyboardButton(text=display_name, callback_data=SelectLangCb(code=code).pack()))

        # Organize buttons in 2 columns
        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons[i : i + 2] for i in range(0, len(buttons), 2)])

        # Add Crowdin link
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text=_("Help us translate!"), url="https://crowdin.com/project/sophiebot")]
        )

        await message.reply(text, reply_markup=keyboard)


class LanguageCallbackHandler(SophieCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (SelectLangCb.filter(), UserRestricting(admin=True))

    async def handle(self) -> Any:
        callback_data: SelectLangCb = self.callback_data

        lang_code = callback_data.code
        i18n = get_i18n()

        if lang_code not in i18n.available_locales:
            await self.event.answer(_("Language not found."), show_alert=True)
            return

        # Update ChatModel using connection
        chat = self.connection.db_model
        if chat:
            chat.language_code = lang_code
            await chat.save()

        locale = i18n.babels.get(lang_code)
        display_name = i18n.locale_display(locale) if locale else lang_code

        await self.event.answer(_("Language changed to {lang}").format(lang=display_name))

        # Re-render the keyboard to show the new checkmark
        buttons = []
        for code in i18n.available_locales:
            babel_locale = i18n.babels.get(code)
            d_name = i18n.locale_display(babel_locale) if babel_locale else code

            stats = i18n.get_locale_stats(code)

            if stats and stats.percent_translated() < 100:
                d_name += f" ({stats.percent_translated()}%)"

            if code == lang_code:
                d_name = f"✅ {d_name}"

            buttons.append(InlineKeyboardButton(text=d_name, callback_data=SelectLangCb(code=code).pack()))

        keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons[i : i + 2] for i in range(0, len(buttons), 2)])
        keyboard.inline_keyboard.append(
            [InlineKeyboardButton(text=_("Help us translate!"), url="https://crowdin.com/project/sophiebot")]
        )

        if self.event.message and isinstance(self.event.message, Message):
            await self.event.message.edit_text(
                _("Language set to {lang}").format(lang=display_name), reply_markup=keyboard
            )

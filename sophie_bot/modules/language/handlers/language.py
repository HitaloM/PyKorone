from aiogram import Router
from aiogram.filters.callback_data import CallbackData
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from aiogram import flags
from aiogram.handlers import MessageHandler, CallbackQueryHandler

from sophie_bot.db.models.chat import ChatModel
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.utils.i18n import get_i18n, gettext as _, lazy_gettext as l_

router = Router(name="language")


class SelectLangCb(CallbackData, prefix="set_lang"):
    code: str


@flags.help(description=l_("Change the language of the bot in the chat."))
class LanguageHandler(MessageHandler):
    @staticmethod
    def filters():
        return (CMDFilter("lang"), UserRestricting(admin=True))

    async def handle(self) -> None:
        message: Message = self.event
        i18n = get_i18n()

        # Get current chat language
        chat = await ChatModel.get_by_tid(message.chat.id)
        current_lang_code = chat.language_code if chat else i18n.default_locale

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


class LanguageCallbackHandler(CallbackQueryHandler):
    @staticmethod
    def filters():
        return (SelectLangCb.filter(), UserRestricting(admin=True))

    async def handle(self) -> None:
        query: CallbackQuery = self.event
        callback_data: SelectLangCb | None = self.data.get("callback_data")

        if not callback_data:
            return

        lang_code = callback_data.code
        i18n = get_i18n()

        if lang_code not in i18n.available_locales:
            await query.answer(_("Language not found."), show_alert=True)
            return

        # Update ChatModel
        if query.message and query.message.chat:
            chat = await ChatModel.get_by_tid(query.message.chat.id)
        else:
            chat = None

        if chat:
            chat.language_code = lang_code
            await chat.save()

            # Update connection for immediate effect if needed,
            # but usually middleware handles it on next request.
            # However, for the reply we might want to switch context?
            # i18n middleware should handle `chat.language_code`

        locale = i18n.babels.get(lang_code)
        display_name = i18n.locale_display(locale) if locale else lang_code

        await query.answer(_("Language changed to {lang}").format(lang=display_name))

        # Edit the message to show new selection
        # We need to manually switch locale for this response to match selected language immediately?
        # Or just keep it in previous language? Usually it's better to confirm in the new language or keep context.
        # Let's simple edit the text.

        # To reply in new language immediately we would need to manually set context,
        # but let's just confirm.

        # We'll re-render the keyboard to show the new checkmark
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

        if query.message and isinstance(query.message, Message):
            await query.message.edit_text(_("Language set to {lang}").format(lang=display_name), reply_markup=keyboard)

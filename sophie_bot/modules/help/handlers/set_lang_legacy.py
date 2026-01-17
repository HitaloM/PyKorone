from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery, Message
from sophie_bot.modules.language.handlers.language import SelectLangCb
from sophie_bot.utils.i18n import get_i18n, gettext as _


async def set_lang_cb(event: CallbackQuery):
    i18n = get_i18n()
    buttons = []

    # Simple recreation of language selection keyboard
    # Note: we don't check DB here as simple fallback/helper

    for code in i18n.available_locales:
        locale = i18n.babels.get(code)
        display_name = i18n.locale_display(locale) if locale else code
        buttons.append(InlineKeyboardButton(text=display_name, callback_data=SelectLangCb(code=code).pack()))

    keyboard = InlineKeyboardMarkup(inline_keyboard=[buttons[i : i + 2] for i in range(0, len(buttons), 2)])

    if event.message and isinstance(event.message, Message):
        await event.message.edit_text(_("Select your language:"), reply_markup=keyboard)

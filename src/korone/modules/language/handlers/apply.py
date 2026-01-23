from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import InlineKeyboardButton, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from stfu_tg import Doc

from korone import aredis
from korone.config import CONFIG
from korone.db.models.language import LanguageModel
from korone.filters.admin_rights import UserRestricting
from korone.modules.language.callbacks import SetLangCallback
from korone.modules.utils_.callbacks import GoToStartCallback
from korone.utils.handlers import KoroneCallbackQueryHandler
from korone.utils.i18n import I18nNew, get_i18n
from korone.utils.i18n import gettext as _


async def set_chat_language(chat_id: int, language: str) -> None:
    await LanguageModel.set_locale(chat_id, language)

    await aredis.delete(f"lang_cache_{chat_id}")

    cache_key = f"cache_get_locale_name:{chat_id}"
    await aredis.delete(cache_key)


def build_language_changed_message(language: str, i18n: I18nNew) -> str:
    locale = i18n.babels.get(language) or i18n.babel(language)
    locale_display = i18n.locale_display(locale)

    text = Doc(_("Language changed to {new_lang}.").format(new_lang=locale_display))

    if language in CONFIG.devs_managed_languages:
        text += _("This is the bot's native language.")
        text += _("If you find any errors, please file an issue in the GitHub Repository.")
    elif stats := i18n.get_locale_stats(locale_code=language):
        percent = stats.percent_translated()
        text += _("The language is {percent}% translated.").format(percent=percent)

        if percent > 99:
            text += _("In case you find any errors, please file an issue in the GitHub Repository.")
        else:
            text += _("Please help us translate this language by completing it on our translations platform.")

    return str(text)


def build_keyboard(language: str, i18n: I18nNew, back_to_start: bool = False) -> InlineKeyboardBuilder:
    keyboard = InlineKeyboardBuilder()

    if language in CONFIG.devs_managed_languages:
        keyboard.button(text=_("🐞 Open GitHub Issues"), url=f"{CONFIG.github_issues}")
    elif (stats := i18n.get_locale_stats(locale_code=language)) and stats.percent_translated() > 99:
        keyboard.button(text=_("🐞 Open GitHub Issues"), url=f"{CONFIG.github_issues}")
    else:
        keyboard.button(text=_("🌍 Help Translate"), url=CONFIG.translation_url)

    if back_to_start:
        keyboard.row(InlineKeyboardButton(text=_("⬅️ Back"), callback_data=GoToStartCallback().pack()))

    return keyboard


@flags.help(exclude=True)
class ApplyLanguageHandler(KoroneCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (SetLangCallback.filter(), UserRestricting(admin=True))

    async def handle(self) -> Any:
        if not self.event.data:
            await self.event.answer(_("Something went wrong."))
            return

        callback_data: SetLangCallback = self.callback_data
        language = callback_data.lang
        back_to_start = callback_data.back_to_start

        message = self.event.message
        if not isinstance(message, Message) or not message.chat:
            return

        chat_id = message.chat.id

        await set_chat_language(chat_id, language)

        i18n = get_i18n()
        text = build_language_changed_message(language, i18n)
        keyboard = build_keyboard(language, i18n, back_to_start)

        await message.edit_text(text, reply_markup=keyboard.as_markup(), disable_web_page_preview=True)

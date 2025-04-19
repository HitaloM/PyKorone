# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>


from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.enums import ChatType
from hydrogram.types import CallbackQuery

from korone import constants
from korone.decorators import router
from korone.filters import UserIsAdmin
from korone.modules.languages.callback_data import SetLangCallback
from korone.modules.languages.database import set_chat_language
from korone.utils.caching import cache
from korone.utils.i18n import I18nNew, get_i18n
from korone.utils.i18n import gettext as _


@router.callback_query(SetLangCallback.filter() & UserIsAdmin)
async def set_lang_callback(client: Client, callback: CallbackQuery) -> None:
    if not callback.data:
        await callback.answer(_("Something went wrong."))
        return

    language = SetLangCallback.unpack(callback.data).lang
    is_private = callback.message.chat.type == ChatType.PRIVATE

    await set_chat_language(is_private, callback, language)
    await cache.delete(f"fetch_locale:{callback.message.chat.id}")

    i18n = get_i18n()
    text = _build_language_changed_message(language, i18n)
    keyboard = _build_keyboard(language, i18n)

    if not keyboard:
        await callback.message.edit(text, disable_web_page_preview=True)
        return

    await callback.message.edit(
        text, reply_markup=keyboard.as_markup(), disable_web_page_preview=True
    )


def _build_language_changed_message(language: str, i18n: I18nNew) -> str:
    text = _("Language changed to {new_lang}.", locale=language).format(
        new_lang=i18n.locale_display(i18n.babel(language))
    )

    if language == i18n.default_locale:
        text += _(
            "\nThis is the bot's native language."
            "\nIf you find any errors, please file an issue in the "
            "GitHub Repository.",
            locale=language,
        )
    elif stats := i18n.get_locale_stats(locale_code=language):
        text += _(
            "\nThe language is {percent}% translated.",
            locale=language,
        ).format(percent=stats.percent_translated)

        text += _get_translation_status_message(stats.percent_translated, language)

    return text


def _get_translation_status_message(percent_translated: int, language: str) -> str:
    if percent_translated > 99:
        return _(
            "\nIn case you find any errors, please file an issue in the GitHub Repository.",
            locale=language,
        )
    return _(
        "\nPlease help us translate this language by completing it on our translations platform.",
        locale=language,
    )


def _build_keyboard(language: str, i18n: I18nNew) -> InlineKeyboardBuilder:
    keyboard = InlineKeyboardBuilder()

    button_text, button_url = _get_button_text_and_url(language, i18n)
    keyboard.button(text=button_text, url=button_url)

    return keyboard


def _get_button_text_and_url(language: str, i18n: I18nNew) -> tuple[str, str]:
    if language == i18n.default_locale or (
        (stats := i18n.get_locale_stats(locale_code=language)) and stats.percent_translated > 99
    ):
        return _("🐞 Open GitHub", locale=language), f"{constants.GITHUB_URL}/issues"
    return _("🌍 Open Translations", locale=language), constants.TRANSLATIONS_URL

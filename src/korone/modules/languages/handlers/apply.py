# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.enums import ChatType
from hydrogram.types import CallbackQuery

from korone import cache, constants
from korone.decorators import router
from korone.filters import IsAdmin
from korone.modules.languages.callback_data import SetLangCallback
from korone.modules.languages.database import set_chat_language
from korone.utils.i18n import get_i18n
from korone.utils.i18n import gettext as _


@router.callback_query(SetLangCallback.filter() & IsAdmin)
async def set_lang_callback(client: Client, callback: CallbackQuery) -> None:
    if not callback.data:
        await callback.answer(_("Something went wrong."))
        return

    language = SetLangCallback.unpack(callback.data).lang
    is_private = callback.message.chat.type == ChatType.PRIVATE

    await set_chat_language(is_private, callback, language)
    await cache.delete(f"fetch_locale:{callback.message.chat.id}")

    i18n = get_i18n()
    text = _("Language changed to {new_lang}.", locale=language).format(
        new_lang=i18n.locale_display(i18n.babel(language))
    )

    keyboard = InlineKeyboardBuilder()
    if language == i18n.default_locale:
        text += _(
            "\nThis is the bot's native language."
            "\nIf you find any errors, please file an issue in the "
            "GitHub Repository.",
            locale=language,
        )
        keyboard.button(
            text=_("🐞 Open GitHub", locale=language),
            url=f"{constants.GITHUB_URL}/issues",
        )
    else:
        stats = i18n.get_locale_stats(locale_code=language)
        if stats:
            text += _(
                "\nThe language is {percent}% translated.",
                locale=language,
            ).format(percent=stats.percent_translated)

            if stats.percent_translated > 99:
                text += _(
                    "\nIn case you find any errors, please "
                    "file an issue in the GitHub Repository.",
                    locale=language,
                )
                keyboard.button(
                    text=_("🐞 Open GitHub", locale=language),
                    url=f"{constants.GITHUB_URL}/issues",
                )
            else:
                text += _(
                    "\nPlease help us translate this language by completing it on "
                    "our translations platform.",
                    locale=language,
                )
                keyboard.button(
                    text=_("🌍 Open Translations", locale=language),
                    url=constants.TRANSLATIONS_URL,
                )

    await callback.message.edit(
        text,
        reply_markup=keyboard.as_markup() if keyboard else None,  # type: ignore
        disable_web_page_preview=True,
    )

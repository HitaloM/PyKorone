# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.enums import ChatType
from hydrogram.types import CallbackQuery

from korone import cache, constants
from korone.decorators import router
from korone.filters import IsAdmin
from korone.handlers.abstract import CallbackQueryHandler
from korone.modules.languages.callback_data import SetLangCallback
from korone.modules.languages.database import set_chat_language
from korone.utils.i18n import get_i18n
from korone.utils.i18n import gettext as _


class ApplyLanguage(CallbackQueryHandler):
    @router.callback_query(SetLangCallback.filter() & IsAdmin)
    async def handle(self, client: Client, callback: CallbackQuery) -> None:
        if not callback.data:
            await callback.answer(_("Something went wrong."))
            return

        is_private = callback.message.chat.type == ChatType.PRIVATE
        language: str = SetLangCallback.unpack(callback.data).lang

        await set_chat_language(is_private, callback, language)

        chat = callback.message.chat
        cache_key = f"fetch_locale:{chat.id}"
        await cache.delete(cache_key)

        text, keyboard = await self.prepare_response(language)

        await callback.message.edit(
            text,
            reply_markup=keyboard.as_markup() if keyboard else None,  # type: ignore
            disable_web_page_preview=True,
        )

    @staticmethod
    async def prepare_response(language: str) -> tuple[str, InlineKeyboardBuilder | None]:
        i18n = get_i18n()

        text = _("Language changed to {new_lang}.", locale=language).format(
            new_lang=i18n.locale_display(i18n.babel(language))
        )

        keyboard = None
        if language == i18n.default_locale:
            keyboard = InlineKeyboardBuilder()
            text += _(
                "\nThis is the bot's native language."
                "\nIf you find any errors, please file a issue in the "
                "GitHub Repository.",
                locale=language,
            )
            keyboard.button(
                text=_("🐞 Open GitHub", locale=language),
                url=f"{constants.GITHUB_URL}/issues",
            )
            return text, keyboard

        stats = i18n.get_locale_stats(locale_code=language)
        if not stats:
            return text, keyboard

        keyboard = InlineKeyboardBuilder()
        percent = 100 if i18n.default_locale == language else stats.percent_translated
        text += _(
            "\nThe language is {percent}% translated.",
            locale=language,
        ).format(percent=percent)
        if percent > 99:
            text += _(
                "\nIn case you find any errors, please file a issue in the " "GitHub Repository.",
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

        return text, keyboard

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from datetime import timedelta

from babel import Locale, UnknownLocaleError
from hydrogram.enums import ChatType
from hydrogram.types import Chat, User

from korone import cache, i18n
from korone.handlers.database.manager import DatabaseManager


class LanguageManager:
    """
    Language manager class to manage the language used by the bot.

    This class is used to manage the language of the bot. It has a method to get the locale
    based on the user or chat object. It also has a method to check if the chat is valid.
    """

    __slots__ = ("database_manager",)

    def __init__(self) -> None:
        self.database_manager = DatabaseManager()

    @staticmethod
    def _is_valid_chat(chat: User | Chat) -> bool:
        """
        Check if the chat is valid.

        This method checks if the chat is valid. If the chat is a user and not a bot, it returns
        True. If the chat is a group or supergroup, it returns True. Otherwise, it returns False.

        Parameters
        ----------
        chat : User | Chat
            The chat object.

        Returns
        -------
        bool
            True if the chat is valid, False otherwise.
        """
        is_user = isinstance(chat, User) and not chat.is_bot
        is_group_or_supergroup = isinstance(chat, Chat) and chat.type in {
            ChatType.GROUP,
            ChatType.SUPERGROUP,
        }
        return is_user or is_group_or_supergroup

    @cache(ttl=timedelta(days=1), key="get_locale:{chat.id}")
    async def get_locale(self, chat: User | Chat) -> str:
        """
        Get the locale based on the user and message.

        This method returns the locale based on the user and message. If the user or chat
        is not a bot, it retrieves the database object and gets the locale from it. If the
        database object is empty, it returns the default locale. If the locale is not available,
        it returns the default locale.

        Parameters
        ----------
        chat : User | Chat
            The user or chat object.

        Returns
        -------
        str
            The locale based on the user or chat.

        Raises
        ------
        UnknownLocaleError
            If the locale identifier is invalid.
        """
        if not self._is_valid_chat(chat):
            return i18n.default_locale

        db_obj = await self.database_manager.get(chat)
        if not db_obj:
            return i18n.default_locale

        try:
            language = db_obj[0]["language"]
            sep = "-" if "_" not in language else "_"
            locale_obj = Locale.parse(language, sep=sep)
            locale = f"{locale_obj.language}_{locale_obj.territory}"
            is_valid_locale = isinstance(locale_obj, Locale) and locale in i18n.available_locales

            if not is_valid_locale:
                msg = "Invalid locale identifier"
                raise UnknownLocaleError(msg)

        except UnknownLocaleError:
            locale = i18n.default_locale

        return str(locale)

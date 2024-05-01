# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from collections.abc import Callable
from functools import wraps

from babel import Locale, UnknownLocaleError
from hydrogram.enums import ChatType
from hydrogram.types import CallbackQuery, Message, User

from korone import i18n
from korone.database.table import Documents
from korone.decorators.database import DatabaseManager


class LocaleManager:
    """
    LocaleManager class to handle i18n operations.

    This class is responsible for handling internationalization (i18n) operations.
    It provides methods to retrieve the locale from a document, handle localization for
    decorated functions, and manage the available locales. It is designed to be used in
    conjunction with the Factory decorator to provide localization support for the
    decorated functions.

    Attributes
    ----------
    database_manager : DatabaseManager
        An instance of the DatabaseManager class.
    """

    __slots__ = ("database_manager",)

    def __init__(self) -> None:
        self.database_manager = DatabaseManager()

    @staticmethod
    def get_locale(db_obj: Documents) -> str:
        """
        Get the locale from a document.

        This method retrieves the locale from the specified document.
        If the locale is not valid, it falls back to the default locale.

        Parameters
        ----------
        db_obj : Documents
            The document object.

        Returns
        -------
        str
            The locale string.
        """

        try:
            if "_" not in db_obj[0]["language"]:
                locale = (
                    Locale.parse(db_obj[0]["language"], sep="-") if db_obj else i18n.default_locale
                )
            else:
                locale = Locale.parse(db_obj[0]["language"])

            if isinstance(locale, Locale):
                locale = f"{locale.language}_{locale.territory}"
            if locale not in i18n.available_locales:
                raise UnknownLocaleError("Invalid locale identifier")

        except UnknownLocaleError:
            locale = i18n.default_locale

        return locale

    def use_gettext(self, func: Callable) -> Callable:
        """
        Decorator to handle localization.

        This method is a decorator that handles localization for the decorated function.
        It retrieves the user or chat object, determines the locale, and sets the appropriate
        context and locale for the function execution.

        Parameters
        ----------
        func : Callable
            The function to be decorated.

        Returns
        -------
        Callable
            The decorated function.
        """

        @wraps(func)
        async def wrapper(*args, **kwargs):
            update: Message | CallbackQuery = args[2]
            is_callback = isinstance(update, CallbackQuery)
            message = update.message if is_callback else update

            db_user = None
            db_chat = None

            user: User = update.from_user if is_callback else message.from_user

            if user and not user.is_bot:
                db_user = await self.database_manager.get_or_insert(
                    "Users",
                    user,
                    user.language_code or i18n.default_locale,
                )
            if message.chat and message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
                db_chat = await self.database_manager.get_or_insert(
                    "Groups",
                    message.chat,
                    i18n.default_locale,
                )

            db_obj = db_user if message.chat.type == ChatType.PRIVATE else db_chat
            locale = LocaleManager.get_locale(db_obj) if db_obj else i18n.default_locale

            with i18n.context(), i18n.use_locale(locale):
                return await func(*args, **kwargs)

        return wrapper

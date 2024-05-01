# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

import time
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps

from babel import Locale, UnknownLocaleError
from hydrogram.enums import ChatType
from hydrogram.filters import Filter
from hydrogram.handlers import CallbackQueryHandler, MessageHandler
from hydrogram.types import CallbackQuery, Chat, Message, User

from korone import i18n
from korone.database.impl import SQLite3Connection
from korone.database.query import Query
from korone.database.table import Document, Documents


@dataclass(frozen=True, slots=True)
class HandlerObject:
    """
    A dataclass to store information about the handler.

    This dataclass is used to store information about the handler, it stores
    the function, the filters, the group number and the event name.
    """

    func: Callable
    """The function to be executed when the event is triggered.

    :type: collections.abc.Callable
    """
    filters: Filter
    """The filter object used to determine if the function should be executed.

    :type: hydrogram.filters.Filter
    """
    group: int
    """The group number for the function, used for ordering the execution of
    multiple functions.

    :type: int
    """
    event: Callable
    """The event handler.

    :type: collections.abc.Callable
    """


class Factory:
    """
    Factory class to create decorators.

    This class is used to create a decorator, it receives the name of the event
    as a parameter and returns the class that will be used to create the
    decorator.

    Parameters
    ----------
    event_name : str
        The name of the event.

    Attributes
    ----------
    event_name : str
        The name of the event.
    events_observed : dict
        A dictionary that stores the events observed by the factory.
    """

    __slots__ = ("event_name", "events_observed")

    def __init__(self, event_name: str) -> None:
        self.event_name = event_name

        self.events_observed = {
            "message": MessageHandler,
            "callback_query": CallbackQueryHandler,
        }

    def __call__(self, filters: Filter, group: int = 0) -> Callable:
        """
        Execute the decorator when the decorated function is called.

        This method is used to create a decorator, it receives the filters and
        the group number as parameters and returns the decorator.

        Parameters
        ----------
        filters : hydrogram.filters.Filter
            The filter object used to determine if the decorated function should be executed.
        group : int, optional
            The group number for the decorated function, used for ordering the execution of
            multiple decorated functions.

        Returns
        -------
        collections.abc.Callable
            The decorated function.
        """

        def wrapper(func: Callable) -> Callable:
            func.on = self.event_name
            func.group = group
            func.filters = filters
            func.handlers = HandlerObject(
                func, filters, group, self.events_observed[self.event_name]
            )

            return self.use_gettext(func)

        return wrapper

    async def create_document(self, chat: User | Chat, language: str) -> Document:
        """
        Create a document object.

        This method creates a document object with the given chat, language, and current time.

        Parameters
        ----------
        chat : Union[User, Chat]
            The chat object.
        language : str
            The language of the document.

        Returns
        -------
        Document
            The created document object.
        """

        return Document(
            id=chat.id,
            username=chat.username if isinstance(chat, User) else "",
            type=chat.type.name.lower() if isinstance(chat, Chat) else None,
            language=language,
            registry_date=int(time.time()),
        )

    async def get_or_insert(self, table_name: str, chat: User | Chat, language: str) -> Documents:
        """
        Get or insert a document into a table.

        This method retrieves a document from the specified table based on the chat ID.
        If the document does not exist, it creates a new document and inserts it into the table.

        Parameters
        ----------
        table_name : str
            The name of the table.
        chat : Union[User, Chat]
            The chat object.
        language : str
            The language of the document.

        Returns
        -------
        Documents
            The retrieved or inserted document.
        """

        async with SQLite3Connection() as conn:
            table = await conn.table(table_name)
            query = Query()
            obj = await table.query(query.id == chat.id)

            if not obj:
                doc = await self.create_document(chat, language)
                await table.insert(doc)
                obj = [doc]

            return Documents(obj)

    def get_locale(self, db_obj: Documents) -> str:
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
                db_user = await self.get_or_insert(
                    "Users",
                    user,
                    user.language_code or i18n.default_locale,
                )
            if message.chat and message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
                db_chat = await self.get_or_insert(
                    "Groups",
                    message.chat,
                    i18n.default_locale,
                )

            db_obj = db_user if message.chat.type == ChatType.PRIVATE else db_chat
            locale = self.get_locale(db_obj) if db_obj else i18n.default_locale

            with i18n.context(), i18n.use_locale(locale):
                return await func(*args, **kwargs)

        return wrapper

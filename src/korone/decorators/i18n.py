# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

import time
from collections.abc import Callable
from functools import wraps

from babel import Locale, UnknownLocaleError
from hydrogram.enums import ChatType
from hydrogram.types import CallbackQuery, Chat, Message, User

from korone import i18n
from korone.database.impl import SQLite3Connection
from korone.database.query import Query
from korone.database.table import Document, Documents


async def get_or_insert(table_name: str, chat: User | Chat, language: str) -> Documents:
    """
    Get or insert a document into the specified table.

    This function retrieves a document from the specified table based on the chat ID.
    If the document does not exist, a new document is inserted into the table with the
    provided chat ID, chat type, language, and registry date.

    Parameters
    ----------
    table_name : str
        The name of the table.
    chat : hydrogram.types.User or hydrogram.types.Chat
        The user or chat object.
    language : str
        The language of the document.

    Returns
    -------
    Documents
        The inserted or retrieved document.
    """
    async with SQLite3Connection() as conn:
        table = await conn.table(table_name)
        query = Query()
        obj = await table.query(query.id == chat.id)

        if not obj:
            doc = Document(
                id=chat.id,
                type=chat.type.name.lower() if isinstance(chat, Chat) else None,
                language=language,
                registry_date=int(time.time()),
            )

            await table.insert(doc)

            obj = [doc]

        return Documents(obj)


def use_gettext(func: Callable) -> Callable:
    """
    Decorator for using gettext.

    This decorator sets the appropriate locale for the function based on the user's language code.
    If the user's locale is not available, it falls back to the default locale.

    Parameters
    ----------
    func : collections.abc.Callable
        The function to be decorated.

    Returns
    -------
    collections.abc.Callable
        The decorated function.

    Raises
    ------
    babel.UnknownLocaleError
        If the locale identifier is invalid.
    """

    @wraps(func)
    async def wrapper(*args, **kwargs):
        update: Message | CallbackQuery = args[2]
        is_callback = isinstance(update, CallbackQuery)
        message = update.message if is_callback else update

        db_user = None
        db_chat = None

        user: User = update.from_user if is_callback else message.from_user

        if user and not user.is_bot and message.chat.type == ChatType.PRIVATE:
            db_user = await get_or_insert(
                "Users",
                user,
                user.language_code if user.language_code else i18n.default_locale,
            )
        if message.chat and message.chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
            db_chat = await get_or_insert(
                "Groups",
                message.chat,
                i18n.default_locale,
            )

        db_obj = db_user or db_chat
        if db_obj:
            try:
                if "_" not in db_obj[0]["language"]:
                    locale = (
                        Locale.parse(db_obj[0]["language"], sep="-")
                        if db_obj
                        else i18n.default_locale
                    )
                else:
                    locale = Locale.parse(db_obj[0]["language"])

                if isinstance(locale, Locale):
                    locale = f"{locale.language}_{locale.territory}"
                if locale not in i18n.available_locales:
                    raise UnknownLocaleError("Invalid locale identifier")

            except UnknownLocaleError:
                locale = i18n.default_locale

        else:
            locale = i18n.default_locale

        with i18n.context(), i18n.use_locale(locale):
            return await func(*args, **kwargs)

    return wrapper

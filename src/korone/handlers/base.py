# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import inspect
import time
from collections.abc import Callable
from datetime import timedelta

from babel import Locale, UnknownLocaleError
from hydrogram import Client
from hydrogram.enums import ChatType
from hydrogram.filters import Filter
from hydrogram.types import CallbackQuery, Chat, Message, Update, User

from korone import cache, i18n
from korone.config import ConfigManager
from korone.database.query import Query
from korone.database.sqlite import SQLite3Connection
from korone.database.table import Document, Documents, Table

BOT_ID: int = ConfigManager.get("hydrogram", "BOT_TOKEN").split(":", 1)[0]


class BaseHandler:
    """
    A base handler for processing updates in the Korone.

    This class provides the base functionality for handling updates in the Korone. It includes
    methods for getting the locale of an update, saving user or chat information to the database,
    and handling updates based on the update type.

    Parameters
    ----------
    callback : Callable
        The callback function to execute for the update.
    filters : Filter | None, optional
        The filters to apply to the update, by default None.
    """

    __slots__ = ("callback", "filters")

    def __init__(self, callback: Callable, filters: Filter | None = None) -> None:
        self.callback = callback
        self.filters = filters

    @staticmethod
    async def _get_message_and_user_from_update(update: Update) -> tuple[Message, User]:
        """
        Get the message and user from an update.

        This method extracts the message and user from an update, handling both messages and
        callback queries.

        Parameters
        ----------
        update : Update
            The update to extract the message and user from.

        Returns
        -------
        tuple[Message, User]
            The message and user extracted from the update.

        Raises
        ------
        ValueError
            If the update type is invalid.
        """
        if isinstance(update, CallbackQuery):
            return update.message, update.from_user
        if isinstance(update, Message):
            return update, update.from_user
        msg = f"Invalid update type: {type(update)}"
        raise ValueError(msg)

    async def _get_locale(self, update: Update) -> str:
        """
        Get the locale for an update.

        This method determines the locale to use for an update based on the update's origin. It
        retrieves the locale from the database for private chats and groups, falling back to the
        default locale if no locale is found.

        Parameters
        ----------
        update : Update
            The update to get the locale for.

        Returns
        -------
        str
            The locale to use for the update.
        """
        message, user = await self._get_message_and_user_from_update(update)
        chat = message.chat

        if user and chat.type == ChatType.PRIVATE:
            return await self._get_locale_from_db(user)
        if chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
            return await self._get_locale_from_db(chat)
        return i18n.default_locale

    @cache(ttl=timedelta(days=1), key="get_locale:{chat.id}")
    async def _get_locale_from_db(self, chat: User | Chat) -> str:
        """
        Get the locale for a chat.

        This method retrieves the locale for a chat from the database, falling back to the default
        locale if no locale is found.

        Parameters
        ----------
        chat : User | Chat
            The chat to get the locale for.

        Returns
        -------
        str
            The locale to use for the chat.

        Raises
        ------
        UnknownLocaleError
            If the locale retrieved from the database is invalid.
        """
        if not self._is_valid_chat(chat):
            return i18n.default_locale

        db_obj = await self._get_document(chat)
        if not db_obj:
            return i18n.default_locale

        try:
            language = db_obj[0]["language"]
            sep = "-" if "_" not in language else "_"
            locale_obj = Locale.parse(language, sep=sep)
            locale = f"{locale_obj.language}_{locale_obj.territory}"
            if locale not in i18n.available_locales:
                msg = "Invalid locale identifier"
                raise UnknownLocaleError(msg)
        except UnknownLocaleError:
            locale = i18n.default_locale

        return str(locale)

    @staticmethod
    def _is_valid_chat(chat: User | Chat) -> bool:
        """
        Check if a chat is valid for locale retrieval.

        This method checks if a chat is valid for retrieving the locale from the database. It
        considers private chats and groups as valid, excluding bots from private chats.

        Parameters
        ----------
        chat : User | Chat
            The chat to check.

        Returns
        -------
        bool
            Whether the chat is valid for locale retrieval.
        """
        is_user = isinstance(chat, User) and not chat.is_bot
        is_group_or_supergroup = isinstance(chat, Chat) and chat.type in {
            ChatType.GROUP,
            ChatType.SUPERGROUP,
        }
        return is_user or is_group_or_supergroup

    async def _handle_update(self, client: Client, update: Update) -> Callable | None:
        """
        Handle an update.

        This method handles an update, extracting the message and user from the update and
        processing the message or callback query. It saves the user or chat information to the
        database and checks if the update is a message from a user before calling the handler's
        callback function.

        Parameters
        ----------
        client : Client
            The client instance.
        update : Update
            The update to handle.

        Returns
        -------
        Callable | None
            The handler's callback function if the update is a message from a user, None otherwise.
        """
        try:
            message, user = await self._get_message_and_user_from_update(update)
        except ValueError:
            return None

        if isinstance(update, CallbackQuery):
            await self._save_user_or_chat(user)
        else:
            await self._process_message(message)

        if user and not user.is_bot and message:
            return await self.callback(client, update)
        return None

    async def _check(self, client: Client, update: Update) -> bool:
        """
        Check if an update passes the filters.

        This method checks if an update passes the filters set for the handler. It retrieves the
        message and user from the update and applies the filters to them.

        Parameters
        ----------
        client : Client
            The client instance.
        update : Update
            The update to check.

        Returns
        -------
        bool
            Whether the update passes the filters.
        """
        try:
            message, _ = await self._get_message_and_user_from_update(update)
        except ValueError:
            return False

        if not message or not callable(self.filters):
            return False

        if inspect.iscoroutinefunction(self.filters.__call__):
            return await self.filters(client, update)
        return await client.loop.run_in_executor(client.executor, self.filters, client, update)  # type: ignore

    async def _get_document(self, chat: User | Chat) -> Documents | None:
        """
        Get the document for a chat from the database.

        This method retrieves the document for a chat from the database based on the chat type. It
        returns None if the chat type is not supported.

        Parameters
        ----------
        chat : User | Chat
            The chat to get the document for.

        Returns
        -------
        Documents | None
            The document for the chat if found, None otherwise.
        """
        table_name = self._get_table_name(chat)
        if not table_name:
            return None

        async with SQLite3Connection() as conn:
            table = await conn.table(table_name)
            query = Query()
            return await table.query(query.id == chat.id)

    @staticmethod
    def _get_table_name(chat: User | Chat) -> str | None:
        """
        Get the table name for a chat.

        This method determines the table name to use for a chat based on the chat type. It returns
        None if the chat type is not supported.

        Parameters
        ----------
        chat : User | Chat
            The chat to get the table name for.

        Returns
        -------
        str | None
            The table name for the chat if supported, None otherwise.
        """
        if isinstance(chat, User) or chat.type == ChatType.PRIVATE:
            return "Users"
        return "Groups" if chat.type in {ChatType.GROUP, ChatType.SUPERGROUP} else None

    async def _save_user_or_chat(
        self, user_or_chat: User | Chat, language: str | None = None
    ) -> None:
        """
        Save user or chat information to the database.

        This method saves the user or chat information to the database, updating the language if
        provided or creating a new document if none is found.

        Parameters
        ----------
        user_or_chat : User | Chat
            The user or chat to save.
        language : str | None, optional
            The language to save for the user or chat, by default None.
        """
        table_name = self._get_table_name(user_or_chat)
        if not table_name:
            return

        async with SQLite3Connection() as conn:
            language = language or i18n.default_locale
            table = await conn.table(table_name)
            query = Query()
            obj = await table.query(query.id == user_or_chat.id)

            if obj:
                await self._update_document(user_or_chat, language, table, query, obj)
            else:
                await self._create_and_insert_document(user_or_chat, language, table)

    async def _update_document(
        self, chat: User | Chat, language: str, table: Table, query: Query, obj: Documents
    ) -> Documents:
        """
        Update a document in the database.

        This method updates a document in the database based on the chat, language, table,
        query, and object provided.

        Parameters
        ----------
        chat : User | Chat
            The chat to update the document for.
        language : str
            The language to update the document with.
        table : Table
            The table to update the document in.
        query : Query
            The query to use for updating the document.
        obj : Documents
            The object to update the document with.

        Returns
        -------
        Documents
            The updated document.
        """
        doc = self._create_document(chat, language)
        doc["registry_date"] = obj[0]["registry_date"]
        doc["language"] = obj[0]["language"]

        await table.update(doc, query.id == chat.id)
        return Documents([doc])

    async def _create_and_insert_document(
        self, chat: User | Chat, language: str, table: Table
    ) -> Documents:
        """
        Create and insert a document in the database.

        This method creates a document for a chat and inserts it into the database based on
        the chat, language, and table provided.

        Parameters
        ----------
        chat : User | Chat
            The chat to create the document for.
        language : str
            The language to create the document with.
        table : Table
            The table to insert the document into.

        Returns
        -------
        Documents
            The inserted document.
        """
        doc = self._create_document(chat, language)
        await table.insert(doc)
        return Documents([doc])

    @staticmethod
    def _create_document(chat: User | Chat, language: str) -> Document:
        """
        Create a document for a chat.

        This method creates a document for a chat based on the chat and language provided.

        Parameters
        ----------
        chat : User | Chat
            The chat to create the document for.
        language : str
            The language to create the document with.

        Returns
        -------
        Document
            The created document.
        """
        username = chat.username if isinstance(chat, User) and chat.username else ""
        title = chat.title if isinstance(chat, Chat) else None
        first_name = chat.first_name if isinstance(chat, User) else None
        chat_type = chat.type.name.lower() if isinstance(chat, Chat) else None
        if isinstance(chat, User) and chat.last_name:
            last_name = chat.last_name
        elif isinstance(chat, User):
            last_name = ""
        else:
            last_name = None

        return Document(
            id=chat.id,
            title=title,
            first_name=first_name,
            last_name=last_name,
            username=username,
            type=chat_type,
            language=language,
            registry_date=int(time.time()),
        )

    async def _process_message(self, message: Message) -> None:
        """
        Process a message.

        This method processes a message, handling private and group messages, message updates, and
        member updates.

        Parameters
        ----------
        message : Message
            The message to process.
        """
        await self._handle_private_and_group_message(message)
        chats_to_update = self._handle_message_update(message)
        await self._handle_member_updates(message)
        await self._update_chats(chats_to_update)

    async def _handle_private_and_group_message(self, message: Message) -> None:
        """
        Handle private and group messages.

        This method handles private and group messages, saving the user or chat information to the
        database for the message's origin.

        Parameters
        ----------
        message : Message
            The message to handle.
        """
        if message.from_user and not message.from_user.is_bot:
            await self._save_user_or_chat(message.from_user, message.from_user.language_code)
        if message.chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
            await self._save_user_or_chat(message.chat)

    def _handle_message_update(self, message: Message) -> list[Chat | User]:
        """
        Handle a message update.

        This method handles a message update, extracting the chats or users to update based on the
        message's origin.

        Parameters
        ----------
        message : Message
            The message to handle.

        Returns
        -------
        list[Chat | User]
            The chats or users to update based on the message.
        """
        chats_to_update = []
        if reply_message := message.reply_to_message:
            chats_to_update.extend(self._handle_replied_message(reply_message))
        if message.forward_from or (
            message.forward_from_chat and message.forward_from_chat.id != message.chat.id
        ):
            chats_to_update.append(message.forward_from_chat or message.forward_from)
        return chats_to_update

    async def _handle_member_updates(self, message: Message) -> None:
        """
        Handle member updates in a chat.

        This method handles member updates in a chat, saving the user or chat information to the
        database for new chat members.

        Parameters
        ----------
        message : Message
            The message to handle member updates for.
        """
        if message.new_chat_members:
            for member in message.new_chat_members:
                if not member.is_bot:
                    await self._save_user_or_chat(member, member.language_code)

    async def _update_chats(self, chats: list[Chat | User]) -> None:
        """
        Update chats in the database.

        This method updates the chats in the database based on the chats provided.

        Parameters
        ----------
        chats : list[Chat  |  User]
            The chats to update.
        """
        for chat in chats:
            language = chat.language_code if isinstance(chat, User) else None
            await self._save_user_or_chat(chat, language)

    @staticmethod
    def _handle_replied_message(message: Message) -> list[Chat | User]:
        """
        Handle a replied message.

        This method handles a replied message, extracting the user or chat to update based on the
        replied message's origin.

        Parameters
        ----------
        message : Message
            The message to handle.

        Returns
        -------
        list[Chat | User]
            The chats or users to update based on the replied message.
        """
        chats_to_update = []

        replied_message_user = message.sender_chat or message.from_user
        if (
            replied_message_user
            and replied_message_user.id != BOT_ID
            and (isinstance(replied_message_user, Chat) or not replied_message_user.is_bot)
        ):
            chats_to_update.append(replied_message_user)

        reply_to_forwarded = message.forward_from_chat or message.forward_from
        if (
            reply_to_forwarded
            and reply_to_forwarded.id != BOT_ID
            and (isinstance(reply_to_forwarded, Chat) or not reply_to_forwarded.is_bot)
        ):
            chats_to_update.append(reply_to_forwarded)

        return chats_to_update

    async def _check_and_handle(self, client: Client, update: Update) -> None:
        """
        Check and handle an update.

        This method checks if an update passes the filters and handles it if so. It sets the locale
        for the response based on the update's origin before proceeding with the usual checks and
        handling.

        Parameters
        ----------
        client : Client
            The client instance.
        update : Update
            The update to check and potentially handle.
        """
        locale = await self._get_locale(update)
        with i18n.context(), i18n.use_locale(locale):
            if await self._check(client, update):
                await self._handle_update(client, update)

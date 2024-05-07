# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import time

from hydrogram.enums import ChatType
from hydrogram.types import Chat, User

from korone import i18n
from korone.database.impl import SQLite3Connection
from korone.database.query import Query
from korone.database.table import Document, Documents, Table


class DatabaseManager:
    """
    DatabaseManager class to handle database operations.

    This class is used to handle all operations related to the database on decorators
    Factory and LocaleManager. It provides methods to create a document object and
    get or insert a document into a table.
    """

    @staticmethod
    async def _get_table_name(chat: User | Chat) -> str | None:
        """
        Get the table name based on the chat type.

        This method returns the table name based on the chat type. If the chat is a
        private chat, it returns the "Users" table name. If the chat is a group or
        supergroup, it returns the "Groups" table name. If the chat type is not
        supported, it returns None.

        Parameters
        ----------
        chat : Union[User, Chat]
            The chat object.

        Returns
        -------
        str | None
            The table name if found, else None.
        """
        if isinstance(chat, User) or chat.type == ChatType.PRIVATE:
            return "Users"

        if chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
            return "Groups"

        return None

    async def _update_document(
        self, chat: User | Chat, language: str, table: Table, query: Query, obj: Documents
    ) -> Documents:
        doc = await self._create_document(chat, language)
        doc["registry_date"] = obj[0]["registry_date"]
        doc["language"] = obj[0]["language"]

        await table.update(doc, query.id == chat.id)
        return Documents([doc])

    async def _create_and_insert_document(
        self, chat: User | Chat, language: str, table: Table
    ) -> Documents:
        """
        Create and insert a document into the database.

        This method creates a document object and inserts it into the database table.

        Parameters
        ----------
        chat : User | Chat
            The chat object.
        language : str
            The language of the document.
        table : Table
            The table object.

        Returns
        -------
        Documents
            The created document object.
        """
        doc = await self._create_document(chat, language)
        await table.insert(doc)
        return Documents([doc])

    @staticmethod
    async def _create_document(chat: User | Chat, language: str) -> Document:
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
        username = chat.username or "" if isinstance(chat, User) else chat.username or ""
        chat_type = chat.type.name.lower() if isinstance(chat, Chat) else None

        return Document(
            id=chat.id,
            username=username,
            type=chat_type,
            language=language,
            registry_date=int(time.time()),
        )

    async def get(self, chat: User | Chat) -> Documents | None:
        """
        Get a document from the database.

        This method gets a document from the database based on the chat object.

        Parameters
        ----------
        chat : User | Chat
            The chat object.

        Returns
        -------
        Documents | None
            The document if found, else None.
        """
        table_name = await self._get_table_name(chat)
        if not table_name:
            return None

        async with SQLite3Connection() as conn:
            table = await conn.table(table_name)
            query = Query()
            return await table.query(query.id == chat.id)

    async def update_or_create(
        self, chat: User | Chat, language: str | None = None
    ) -> Documents | None:
        """
        Update or create a document in the database.

        This method updates a document in the database if it exists, otherwise creates a new
        document and inserts it into the database.

        Parameters
        ----------
        chat : User | Chat
            The chat object.
        language : str | None, optional
            The language of the document. By default, it uses the default locale.

        Returns
        -------
        Documents | None
            The updated or created document if successful, else None.
        """
        table_name = await self._get_table_name(chat)
        if not table_name:
            return None

        async with SQLite3Connection() as conn:
            language = language or i18n.default_locale
            table = await conn.table(table_name)
            query = Query()
            obj = await table.query(query.id == chat.id)

            if obj:
                return await self._update_document(chat, language, table, query, obj)

            return await self._create_and_insert_document(chat, language, table)

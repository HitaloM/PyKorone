# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from korone.database.connection import Connection
from korone.database.query import Query
from korone.database.table import Document
from korone.modules.manager import Chat, ChatColumn, Manager, Table


class ChatLanguageManager(Manager[Chat]):
    """
    Manage the language settings for chat objects.

    This class is used to manage the language settings for chat objects.

    Parameters
    ----------
    conn : Connection
        The connection object used for database operations.
    table : Table
        The table object representing the chat table in the database.

    Attributes
    ----------
    columns : dict[ChatColumn, str]
        A dictionary mapping ChatColumn enum values to their corresponding
        column names in the database.
    """

    def __init__(self, conn: Connection, table: Table) -> None:
        super().__init__(conn=conn, table=table)

        self.columns: dict[ChatColumn, str] = {
            ChatColumn.ID: "id",
            ChatColumn.TYPE: "type",
            ChatColumn.LANGUAGE: "language",
            ChatColumn.REGISTRY_DATE: "registrydate",
        }

    def cast(self, fields: Document) -> Chat:
        """
        Convert a document retrieved from the database into a Chat object.

        This method is used to convert a document retrieved from the database into a Chat object.

        Parameters
        ----------
        fields : Document
            The document retrieved from the database.

        Returns
        -------
        hydrogram.types.Chat
            The Chat object created from the document.
        """
        return Chat(
            id=fields[self.columns[ChatColumn.ID]],
            type=fields[self.columns[ChatColumn.TYPE]],
            language=fields[self.columns[ChatColumn.LANGUAGE]],
            registrydate=fields[self.columns[ChatColumn.REGISTRY_DATE]],
        )

    async def get_chat_language(self, chat_id: int) -> Chat:
        """
        Retrieve the language settings for a chat with the given ID.

        This method is used to retrieve the language settings for a chat with the given ID.

        Parameters
        ----------
        chat_id : int
            The ID of the chat.

        Returns
        -------
        hydrogram.types.Chat
            The Chat object representing the language settings for the chat.
        """
        chat = Query()
        chat = await self.query(chat.id == chat_id)
        return self.cast(chat[0])

    async def set_chat_language(self, chat_id: int, language: str) -> None:
        """
        Update the language settings for a chat with the given ID.

        This method is used to update the language settings for a chat with the given ID.

        Parameters
        ----------
        chat_id : int
            The ID of the chat.
        language : str
            The new language setting for the chat.
        """
        chat = Query()
        query = chat.id == chat_id
        document = Document(language=language)
        await self.update(document, query)


async def create_tables(conn: Connection) -> None:
    """
    Create tables for Users and Groups if they do not already exist.

    This method is used to create tables for Users and Groups if they do not already exist.

    Parameters
    ----------
    conn : aiosqlite.Connection
        The connection object used for database operations.
    """
    await conn._execute(
        """
        CREATE TABLE IF NOT EXISTS Users (
            id INTEGER PRIMARY KEY,
            language VARCHAR(2) NOT NULL DEFAULT "en",
            registrydate INTEGER NOT NULL
        )
        """
    )
    await conn._execute(
        """
        CREATE TABLE IF NOT EXISTS Groups (
            id INTEGER PRIMARY KEY,
            type TEXT,
            language VARCHAR(2) NOT NULL DEFAULT "en",
            registrydate INTEGER NOT NULL
        )
        """
    )

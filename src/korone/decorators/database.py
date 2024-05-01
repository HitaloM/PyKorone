# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

import time

from hydrogram.types import Chat, User

from korone.database.impl import SQLite3Connection
from korone.database.query import Query
from korone.database.table import Document, Documents


class DatabaseManager:
    """
    DatabaseManager class to handle database operations.

    This class is used to handle all operations related to the database on decorators
    Factory and LocaleManager. It provides methods to create a document object and
    get or insert a document into a table.
    """

    @staticmethod
    async def create_document(chat: User | Chat, language: str) -> Document:
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

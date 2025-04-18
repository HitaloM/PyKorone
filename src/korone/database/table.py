# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>
# Copyright (c) 2023 Victor Cebarros <https://github.com/victorcebarros>

from __future__ import annotations

from collections import UserDict
from typing import TYPE_CHECKING, Any, NewType, Protocol

if TYPE_CHECKING:
    from .query import Query


class Document(UserDict[str, Any]):
    """A document represents a database record as a dictionary of key-value pairs.

    This class inherits from UserDict to provide dictionary-like functionality
    while allowing for additional methods specific to database documents.
    """

    pass


Documents = NewType("Documents", list[Document])


class Table(Protocol):
    """Protocol defining the interface for database table operations.

    This protocol defines the common operations that can be performed
    on a database table regardless of the underlying database engine.
    """

    async def insert(self, fields: Document) -> None:
        """Insert a new record into the table.

        Args:
            fields: A Document containing the field values to insert
        """
        ...

    async def query(self, query: Query) -> Documents:
        """Query records from the table based on specified criteria.

        Args:
            query: A Query object specifying the selection criteria

        Returns:
            A list of Document objects representing the matching records
        """
        ...

    async def update(self, fields: Document, query: Query) -> None:
        """Update records in the table that match the query.

        Args:
            fields: A Document containing the field values to update
            query: A Query object specifying which records to update
        """
        ...

    async def delete(self, query: Query) -> None:
        """Delete records from the table that match the query.

        Args:
            query: A Query object specifying which records to delete
        """
        ...

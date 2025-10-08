# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>
# Copyright (c) 2023 Victor Cebarros <https://github.com/victorcebarros>

from __future__ import annotations

from typing import TYPE_CHECKING, Any, cast

from korone.database.table import Document, Documents, Table

if TYPE_CHECKING:
    import aiosqlite

    from korone.database.connection import Connection
    from korone.database.query import Query


class SQLite3Table(Table):
    """SQLite3 implementation of the Table protocol.

    This class provides the actual implementation of database table operations
    for SQLite3 databases.

    Attributes:
        _conn: The database connection
        _table: The name of the table
    """

    def __init__(self, conn: Connection, table: str) -> None:
        """Initialize a SQLite3Table instance.

        Args:
            conn: The database connection
            table: The name of the table

        Raises:
            RuntimeError: If the connection is None
        """
        if conn is None:
            msg = "Connection cannot be None"
            raise RuntimeError(msg)

        self._conn = conn
        self._table = table

    async def _execute_and_commit(self, sql: str, params: tuple[Any, ...]) -> None:
        """Execute an SQL statement and commit the changes.

        Args:
            sql: The SQL statement to execute
            params: The parameters to bind to the SQL statement
        """
        await self._conn.execute(sql, params)
        await self._conn.commit()

    async def insert(self, fields: Document) -> None:
        """Insert a new record into the table.

        Args:
            fields: A Document containing the field values to insert

        Notes:
            This method uses INSERT OR IGNORE, which won't raise an error
            if a unique constraint is violated.
        """
        # Filter out None values to avoid inserting NULL for fields that should use DEFAULT
        non_none_items = {k: v for k, v in fields.items() if v is not None}

        if not non_none_items:
            return  # Nothing to insert

        keys = ", ".join(non_none_items.keys())
        values = tuple(non_none_items.values())
        placeholders = ", ".join("?" for _ in values)

        sql = f"INSERT OR IGNORE INTO {self._table} ({keys}) VALUES ({placeholders})"

        await self._execute_and_commit(sql, values)

    async def query(self, query: Query) -> Documents:
        """Query records from the table based on specified criteria.

        Args:
            query: A Query object specifying the selection criteria

        Returns:
            A list of Document objects representing the matching records
        """
        clause, data = query.compile()
        sql = f"SELECT * FROM {self._table} WHERE {clause}"

        cursor: aiosqlite.Cursor = await self._conn.execute(sql, data)
        rows = await cursor.fetchall()

        documents = [
            Document({
                desc[0]: value for desc, value in zip(cursor.description, row, strict=False)
            })
            for row in rows
        ]

        # Cast to Documents to satisfy return type requirements
        return cast("Documents", documents)

    async def query_all(self, limit: int = 100, offset: int = 0) -> Documents:
        """Query all records from the table with pagination.

        Args:
            limit: Maximum number of records to return (default: 100)
            offset: Number of records to skip (default: 0)

        Returns:
            A list of Document objects representing the records
        """
        sql = f"SELECT * FROM {self._table} LIMIT ? OFFSET ?"

        cursor: aiosqlite.Cursor = await self._conn.execute(sql, (limit, offset))
        rows = await cursor.fetchall()

        documents = [
            Document({
                desc[0]: value for desc, value in zip(cursor.description, row, strict=False)
            })
            for row in rows
        ]

        return cast("Documents", documents)

    async def count(self, query: Query | None = None) -> int:
        """Count the number of records that match the query.

        Args:
            query: A Query object specifying the selection criteria,
                  or None to count all records

        Returns:
            The number of records that match the query
        """
        if query is None:
            sql = f"SELECT COUNT(*) FROM {self._table}"
            cursor: aiosqlite.Cursor = await self._conn.execute(sql, ())
        else:
            clause, data = query.compile()
            sql = f"SELECT COUNT(*) FROM {self._table} WHERE {clause}"
            cursor: aiosqlite.Cursor = await self._conn.execute(sql, data)

        result = await cursor.fetchone()
        return result[0] if result else 0

    async def update(self, fields: Document, query: Query) -> None:
        """Update records in the table that match the query.

        Args:
            fields: A Document containing the field values to update
            query: A Query object specifying which records to update
        """
        pairs = [(key, value) for key, value in fields.items() if value is not None]
        if not pairs:
            return  # Nothing to update

        assignments = ", ".join(f"{key} = ?" for key, _ in pairs)
        values = [value for _, value in pairs]

        clause, data = query.compile()
        sql = f"UPDATE {self._table} SET {assignments} WHERE {clause}"

        await self._execute_and_commit(sql, (*values, *data))

    async def delete(self, query: Query) -> None:
        """Delete records from the table that match the query.

        Args:
            query: A Query object specifying which records to delete
        """
        clause, data = query.compile()
        sql = f"DELETE FROM {self._table} WHERE {clause}"

        await self._execute_and_commit(sql, data)

    async def exists(self, query: Query) -> bool:
        """Check if any records match the query.

        Args:
            query: A Query object specifying the selection criteria

        Returns:
            True if at least one record matches the query, False otherwise
        """
        count = await self.count(query)
        return count > 0

    async def get_or_create(self, query: Query, default_values: Document) -> tuple[Document, bool]:
        """Get a record if it exists, or create it if it doesn't.

        Args:
            query: A Query object specifying which record to get
            default_values: Default values to use if creating a new record

        Returns:
            A tuple containing the document and a boolean indicating
            whether the document was created (True) or existed already (False)
        """
        documents = await self.query(query)

        if documents:
            return documents[0], False

        await self.insert(default_values)
        return default_values, True

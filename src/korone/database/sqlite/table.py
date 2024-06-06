# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>
# Copyright (c) 2023 Victor Cebarros <https://github.com/victorcebarros>


from typing import TYPE_CHECKING

from korone.database.connection import Connection
from korone.database.query import Query
from korone.database.table import Document, Documents, Table
from korone.utils.logging import log

if TYPE_CHECKING:
    import aiosqlite


class SQLite3Table(Table):
    """
    Represents the specifics of an SQLite3 Table.

    Represents the specifics of an SQLite3 Table, used internally by SQLite3Connection
    to perform operations on the database.

    Parameters
    ----------
    conn : Connection
        The connection object.
    table : str
        The name of the table.
    """

    def __init__(self, conn: Connection, table: str) -> None:
        if conn is None:
            msg = "Connection cannot be None"
            raise RuntimeError(msg)

        self._conn = conn
        self._table = table

    async def insert(self, fields: Document) -> None:
        """
        Insert a row into the table.

        This method takes a Document object representing the fields to be inserted into the table.
        It constructs an SQL INSERT statement and executes it.

        Parameters
        ----------
        fields : Document
            The fields to be inserted.
        """
        keys = ", ".join(key for key, value in fields.items() if value is not None)
        values = tuple(value for value in fields.values() if value is not None)
        placeholders = ", ".join("?" for _ in values)

        sql = f"INSERT INTO {self._table} ({keys}) VALUES ({placeholders})"

        log.debug("Inserting into table %s: %s", self._table, fields)

        await self._conn.execute(sql, values)
        await self._conn.commit()

    async def query(self, query: Query) -> Documents:
        """
        SQLite3 query execution.

        Query rows that match the criteria specified by the query.

        Parameters
        ----------
        query : Query
            The query that specifies the criteria.

        Returns
        -------
        Documents
            A list of Document objects representing the rows that match the criteria.
        """
        clause, data = query.compile()
        sql = f"SELECT * FROM {self._table} WHERE {clause}"

        log.debug("Querying table %s with clause: %s and data: %s", self._table, clause, data)

        cursor: aiosqlite.Cursor = await self._conn.execute(sql, data)
        rows = await cursor.fetchall()

        documents = [
            Document({
                desc[0]: value for desc, value in zip(cursor.description, row, strict=False)
            })
            for row in rows
        ]

        return Documents(documents)

    async def update(self, fields: Document, query: Query) -> None:
        """
        SQLite3 row update.

        Update fields on rows that match the criteria specified by the query.

        Parameters
        ----------
        fields : Document
            The fields to be updated.
        query : Query
            The query that specifies the criteria.
        """
        pairs = [(key, value) for key, value in fields.items() if value is not None]
        assignments = ", ".join(f"{key} = ?" for key, _ in pairs)
        values = [value for _, value in pairs]

        clause, data = query.compile()
        sql = f"UPDATE {self._table} SET {assignments} WHERE {clause}"

        log.debug("Updating table %s with fields: %s and query: %s", self._table, fields, query)

        await self._conn.execute(sql, (*values, *data))
        await self._conn.commit()

    async def delete(self, query: Query) -> None:
        """
        SQLite3 row deletion.

        Delete rows that match the criteria specified by the query.

        Parameters
        ----------
        query : Query
            The query that specifies the criteria.
        """
        clause, data = query.compile()
        sql = f"DELETE FROM {self._table} WHERE {clause}"

        log.debug("Deleting from table %s with query: %s", self._table, query)

        await self._conn.execute(sql, data)
        await self._conn.commit()

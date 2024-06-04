# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>
# Copyright (c) 2023 Victor Cebarros <https://github.com/victorcebarros>

from pathlib import Path

import aiosqlite

from korone import constants
from korone.database.connection import Connection
from korone.database.query import Query
from korone.database.table import Document, Documents, Table
from korone.utils.logging import log


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

        cursor = await self._conn._execute(sql, data)
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


class SQLite3Connection(Connection):
    """
    Represents a connection to a SQLite database.

    Represents a connection to a SQLite database, providing methods for connecting,
    executing SQL statements, and managing the connection.

    Parameters
    ----------
    path : str, optional
        The path to the SQLite database file, by default constants.DEFAULT_DBFILE_PATH.
    *args
        Additional positional arguments for the `sqlite3.connect` function.
    **kwargs
        Additional keyword arguments for the `sqlite3.connect` function.
    """

    def __init__(self, path: str = constants.DEFAULT_DBFILE_PATH, *args, **kwargs) -> None:
        self._path = path
        self._args = args
        self._kwargs = kwargs
        self._conn: aiosqlite.Connection | None = None

    async def __aenter__(self) -> "SQLite3Connection":
        if not await self._is_open():
            await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.close()

    async def _is_open(self) -> bool:
        return self._conn is not None

    async def _execute(
        self, sql: str, parameters: tuple = (), /, script: bool = False
    ) -> aiosqlite.Cursor:
        if not self._conn:
            msg = "Connection is not open."
            raise RuntimeError(msg)

        log.debug("Executing SQL: %s with parameters: %s", sql, parameters)

        return await (
            self._conn.executescript(sql) if script else self._conn.execute(sql, parameters)
        )

    async def commit(self) -> None:
        """
        SQLite3 transaction commit.

        Commit the current transaction.

        Raises
        ------
        RuntimeError
            If the connection is not yet open.
        """
        if not await self._is_open():
            msg = "Connection is not yet open."
            raise RuntimeError(msg)

        await self._conn.commit()  # type: ignore

    async def connect(self) -> None:
        """
        SQLite3 database connection.

        Connect to the SQLite database and store the connection in the `_conn` attribute.

        Raises
        ------
        RuntimeError
            If the connection is already open.
        """
        if await self._is_open():
            msg = "Connection is already in place."
            raise RuntimeError(msg)

        if not Path(self._path).parent.exists():
            log.info("Creating database directory")
            Path(self._path).parent.mkdir(parents=True, exist_ok=True)

        self._conn = await aiosqlite.connect(self._path, *self._args, **self._kwargs)
        await self._conn.execute("PRAGMA journal_mode=WAL;")

    async def table(self, name: str) -> Table:
        """
        SQLite3 table object retrieval.

        Return a Table object representing the specified table.

        Parameters
        ----------
        name : str
            The name of the table.

        Returns
        -------
        Table
            A Table object representing the specified table.
        """
        return SQLite3Table(conn=self, table=name)

    async def execute(self, sql: str, parameters: tuple = (), script: bool = False) -> None:
        """
        SQL statement execution.

        Execute an SQL statement with optional parameters.

        Parameters
        ----------
        sql : str
            The SQL statement to be executed.
        parameters : tuple, optional
            The parameters to be used in the SQL statement, by default ().
        script : bool, optional
            If True, the SQL statement is treated as a script, by default False.

        Raises
        ------
        RuntimeError
            If the connection is not yet open.
        """
        if not await self._is_open():
            msg = "Connection is not yet open."
            raise RuntimeError(msg)

        await self._execute(sql, parameters, script)

    async def close(self) -> None:
        """
        SQLite3 database connection closure.

        Close the database connection if it is open.

        Raises
        ------
        RuntimeError
            If the connection is not yet open.
        """
        if not await self._is_open():
            msg = "Connection is not yet open."
            raise RuntimeError(msg)

        if self._conn:
            await self._conn.close()
            self._conn = None

    async def vacuum(self) -> None:
        if not await self._is_open():
            msg = "Connection is not yet open."
            raise RuntimeError(msg)

        log.debug("Running VACUUM on the database.")
        if self._conn:
            await self._conn.execute("VACUUM;")
            await self._conn.commit()

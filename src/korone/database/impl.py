# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Victor Cebarros <https://github.com/victorcebarros>
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from pathlib import Path

import aiosqlite

from korone.constants import DEFAULT_DBFILE_PATH
from korone.database.connection import Connection
from korone.database.query import Query
from korone.database.table import Document, Documents, Table
from korone.utils.logging import log


class SQLite3Table:
    """
    Represent the specifics of a SQLitie3 Table.

    This class is used internally by SQLite3Connection
    to perform operations on the database.

    Parameters
    ----------
    conn : _Conn
        The connection object.
    table : str
        The name of the table.
    """

    _conn: Connection
    _table: str

    def __init__(self, *, conn: Connection, table: str) -> None:
        if conn is None:
            raise RuntimeError("Connecton cannot be None")

        self._conn = conn
        self._table = table

    async def insert(self, fields: Document) -> None:
        """
        Insert a row on the table.

        This method inserts a row on the table.

        Parameters
        ----------
        fields : Document
            The fields to be inserted.
        """
        values = tuple(val for val in fields.values() if val is not None)
        placeholders = ", ".join("?" for _ in values)

        sql = f"INSERT INTO {self._table} VALUES ({placeholders})"

        await self._conn.execute(sql, values)
        await self._conn.commit()

    async def query(self, query: Query) -> Documents:
        """
        Query rows that match the criteria.

        This method queries rows that match the criteria
        specified by the query.

        Parameters
        ----------
        query : Query
            The query that specifies the criteria.

        Returns
        -------
        Documents
            A list of Document objects representing the rows
            that match the criteria.
        """
        clause, data = query.compile()

        sql = f"SELECT * FROM {self._table} WHERE {clause}"

        cursor = await self._conn._execute(sql, data)
        rows = await cursor.fetchall()

        documents = [
            Document({
                description[0]: value for description, value in zip(cursor.description, row)
            })
            for row in rows
        ]

        return Documents(documents)

    async def update(self, fields: Document, query: Query) -> None:
        """
        Update fields on rows that match the criteria.

        This method updates the fields of rows that match
        the criteria specified by the query.

        Parameters
        ----------
        fields : Document
            The fields to be updated.
        query : Query
            The query that specifies the criteria.
        """
        pairs = list(fields.items())

        assignments = ", ".join(f"{key} = ?" for key, _ in pairs)
        values = [value for _, value in pairs]

        clause, data = query.compile()

        sql = f"UPDATE {self._table} SET {assignments} WHERE {clause}"

        await self._conn.execute(sql, (*values, *data))
        await self._conn.commit()

    async def delete(self, query: Query) -> None:
        """
        Delete rows that match the criteria.

        This method deletes rows that match the criteria
        specified by the query.

        Parameters
        ----------
        query : Query
            The query that specifies the criteria.
        """
        clause, data = query.compile()

        sql = f"DELETE FROM {self._table} WHERE {clause}"

        await self._conn.execute(sql, data)
        await self._conn.commit()


class SQLite3Connection:
    """
    Represent a connection to a SQLite database.

    This class provides methods for connecting to a SQLite database,
    executing SQL statements, and managing the connection.

    Parameters
    ----------
    *args
        Additional positional arguments for the `sqlite3.connect` function.
    path : Path, optional
        The path to the SQLite database file, by default Path(DEFAULT_DBFILE_PATH).
    **kwargs
        Additional keyword arguments for the `sqlite3.connect` function.

    Attributes
    ----------
    _path : Path
        The path to the SQLite database file.
    _args : tuple
        Additional positional arguments for the `sqlite3.connect` function.
    _kwargs : dict
        Additional keyword arguments for the `sqlite3.connect` function.
    _conn : sqlite3.Connection | None
        The SQLite database connection object.
    """

    _path: str
    _args: tuple
    _kwargs: dict
    _conn: aiosqlite.Connection | None = None

    def __init__(self, *args, path: str = DEFAULT_DBFILE_PATH, **kwargs) -> None:
        self._path = path
        self._args = args
        self._kwargs = kwargs

    async def __aenter__(self) -> "SQLite3Connection":
        await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.close()

    async def _is_open(self) -> bool:
        return self._conn is not None

    async def _execute(
        self, sql: str, parameters: tuple = (), /, script: bool = False
    ) -> aiosqlite.Cursor:
        conn: aiosqlite.Connection = self._conn  # type: ignore

        if self._conn is not None:
            if script:
                return await conn.executescript(sql)
            return await conn.execute(sql, parameters)

        async with conn:
            if script:
                return await conn.executescript(sql)
            return await conn.execute(sql, parameters)

    async def commit(self) -> None:
        """
        Commit the current transaction.

        This method is used to commit the current transaction. If there is no
        current transaction, this method does nothing.

        Raises
        ------
        RuntimeError
            If the connection is not yet open.
        """
        if not await self._is_open():
            raise RuntimeError("Connection is not yet open.")

        await self._conn.commit()  # type: ignore

    async def connect(self) -> None:
        """
        Connect to the SQLite database.

        This method connects to the SQLite database
        and stores the connection in the `_conn` attribute.

        Raises
        ------
        RuntimeError
            If the connection is already in place.
        """
        if await self._is_open():
            raise RuntimeError("Connection is already in place.")

        if not (path := Path(self._path)).parent.exists():
            log.info("Could not find database directory")
            path.parent.mkdir(parents=True, exist_ok=True)
            log.info("Creating database directory")

        self._conn = await aiosqlite.connect(self._path, *self._args, **self._kwargs)

        await self.execute("PRAGMA journal_mode=WAL;")
        await self.commit()
        await self.execute("VACUUM;")
        await self.commit()

    async def table(self, name: str) -> Table:
        """
        Return a Table object representing the specified table.

        This methos returns a Table object representing the
        specified table. The Table object can be used to
        perform queries and other operations on the table.

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

    async def execute(self, sql: str, parameters: tuple = (), /, script: bool = False) -> None:
        """
        Execute an SQL statement with optional parameters.

        Executes an SQL statement with optional parameters.

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
            Raised if the connection is not yet open.
        """
        if not await self._is_open():
            raise RuntimeError("Connection is not yet open.")

        await self._execute(sql, parameters, script)

    async def close(self) -> None:
        """
        Close the database connection.

        This method is automatically called when
        the context manager exits.

        Raises
        ------
        RuntimeError
            If the connection is not yet open.
        """
        if not await self._is_open():
            raise RuntimeError("Connection is not yet open.")

        if self._conn is not None:
            await self._conn.close()
            self._conn = None

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>
# Copyright (c) 2023 Victor Cebarros <https://github.com/victorcebarros>

from pathlib import Path

import aiosqlite

from korone import constants
from korone.database.connection import Connection
from korone.database.sqlite.table import SQLite3Table
from korone.database.table import Table
from korone.utils.logging import log


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
        if not await self.is_open():
            await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.close()

    async def is_open(self) -> bool:
        """
        Check if the connection is open.

        This method checks if the connection is open.

        Returns
        -------
        bool
            True if the connection is open, False otherwise.
        """
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
        if not await self.is_open():
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
        if await self.is_open():
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
        if not await self.is_open():
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
        if not await self.is_open():
            msg = "Connection is not yet open."
            raise RuntimeError(msg)

        if self._conn:
            await self._conn.close()
            self._conn = None

    async def vacuum(self) -> None:
        if not await self.is_open():
            msg = "Connection is not yet open."
            raise RuntimeError(msg)

        log.debug("Running VACUUM on the database.")
        if self._conn:
            await self._conn.execute("VACUUM;")
            await self._conn.commit()

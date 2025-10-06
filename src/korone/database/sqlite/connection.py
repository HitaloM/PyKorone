# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>
# Copyright (c) 2023 Victor Cebarros <https://github.com/victorcebarros>

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Self

import aiosqlite
from anyio import Path

from korone import constants
from korone.database.connection import Connection
from korone.utils.logging import get_logger

from .table import SQLite3Table

if TYPE_CHECKING:
    from types import TracebackType

    from korone.database.table import Table

logger = get_logger(__name__)


class SQLite3Connection(Connection):
    """SQLite3 implementation of the database connection protocol.

    This class implements the Connection protocol for SQLite databases using
    the aiosqlite library, with optimized settings for performance and concurrency.
    """

    def __init__(
        self, path: str = constants.DEFAULT_DBFILE_PATH, *args: Any, **kwargs: Any
    ) -> None:
        """Initialize a SQLite3Connection instance.

        Args:
            path: Path to the SQLite database file
            *args: Additional arguments to pass to aiosqlite.connect
            **kwargs: Additional keyword arguments to pass to aiosqlite.connect
        """
        self._path = path
        self._args = args
        self._kwargs = kwargs
        self._conn: aiosqlite.Connection | None = None

    async def __aenter__(self) -> Self:
        """Enter the async context manager.

        Returns:
            The connection instance

        Notes:
            Automatically connects to the database if not already connected.
        """
        if not await self.is_open():
            await self.connect()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        """Exit the async context manager.

        Args:
            exc_type: The exception type, if any
            exc_value: The exception value, if any
            traceback: The exception traceback, if any

        Notes:
            Automatically closes the connection when exiting the context.
        """
        await self.close()

    async def is_open(self) -> bool:
        """Check if the database connection is open.

        Returns:
            True if the connection is open, False otherwise
        """
        return self._conn is not None

    async def _execute(
        self, sql: str, parameters: tuple[Any, ...] = (), /, *, script: bool = False
    ) -> aiosqlite.Cursor:
        """Execute an SQL statement or script.

        Args:
            sql: The SQL statement or script to execute
            parameters: The parameters to bind to the SQL statement
            script: If True, execute as a script; otherwise as a single statement

        Returns:
            An aiosqlite.Cursor object

        Raises:
            RuntimeError: If the connection is not open
        """
        if not self._conn:
            msg = "Connection is not open"
            raise RuntimeError(msg)

        await logger.adebug("[Database] Executing SQL: %s with parameters: %s", sql, parameters)

        if script:
            return await self._conn.executescript(sql)
        return await self._conn.execute(sql, parameters)

    async def commit(self) -> None:
        """Commit the current transaction.

        Raises:
            RuntimeError: If the connection is not open
        """
        if not await self.is_open():
            msg = "Connection is not yet open"
            raise RuntimeError(msg)

        if self._conn:
            await self._conn.commit()

    async def connect(self) -> None:
        """Open a connection to the database.

        Creates the parent directory if it doesn't exist and sets optimal
        SQLite configuration parameters for performance.

        Raises:
            RuntimeError: If the connection is already open
        """
        if await self.is_open():
            msg = "Connection is already in place"
            raise RuntimeError(msg)

        db_path = Path(self._path)
        parent = db_path.parent
        if not await parent.exists():
            await logger.ainfo("Creating database directory")
            await parent.mkdir(parents=True, exist_ok=True)

        self._conn = await aiosqlite.connect(self._path, *self._args, **self._kwargs)

        await self._conn.execute("PRAGMA journal_mode=WAL;")

        await self._conn.execute("PRAGMA synchronous=NORMAL;")
        await self._conn.execute("PRAGMA foreign_keys=ON;")

    async def table(self, name: str) -> Table:
        """Get a table interface for the given table name.

        Args:
            name: The name of the table

        Returns:
            A Table instance for the requested table
        """
        return SQLite3Table(conn=self, table=name)

    async def execute(
        self, sql: str, parameters: tuple[Any, ...] = (), /, *, script: bool = False
    ) -> aiosqlite.Cursor:
        """Execute an SQL statement or script.

        Args:
            sql: The SQL statement or script to execute
            parameters: The parameters to bind to the SQL statement
            script: If True, execute as a script; otherwise as a single statement

        Returns:
            An aiosqlite.Cursor object
        """
        return await self._execute(sql, parameters, script=script)

    async def close(self) -> None:
        """Close the database connection.

        Raises:
            RuntimeError: If the connection is not open
        """
        if not await self.is_open():
            msg = "Connection is not yet open"
            raise RuntimeError(msg)

        if self._conn:
            await self._conn.close()
            self._conn = None

    async def vacuum(self) -> None:
        """Run the VACUUM command to optimize the database file.

        This reduces the file size and improves performance by rebuilding
        the entire database file and defragmenting the content.

        Raises:
            RuntimeError: If the connection is not open
        """
        if not await self.is_open():
            msg = "Connection is not yet open"
            raise RuntimeError(msg)

        await logger.adebug("Running VACUUM on the database")
        if self._conn:
            await self._conn.execute("VACUUM;")
            await self._conn.commit()

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio
from typing import Optional

from korone import constants
from korone.database.connection import Connection
from korone.database.pool import ConnectionPool
from korone.database.sqlite.connection import SQLite3Connection
from korone.utils.logging import log


class SQLite3ConnectionPool(ConnectionPool):
    """
    SQLite3 Connection Pool.

    Manages a pool of SQLite3 database connections to optimize connection reuse
    and minimize the overhead of opening and closing connections. It follows
    a singleton pattern to ensure only one instance exists.
    """

    __slots__ = (
        "_closing",
        "_conn",
        "_initialize_task",
        "_initialized",
        "_lock",
        "_max_size",
        "_min_size",
        "_path",
        "_pool",
    )

    _instance: Optional["SQLite3ConnectionPool"] = None

    def __new__(cls, *args, **kwargs) -> "SQLite3ConnectionPool":
        """
        Create a new instance of the SQLite3ConnectionPool if one does not already exist.

        Ensures that only one instance of the connection pool exists (singleton pattern).

        Parameters
        ----------
        *args : tuple
            Variable length argument list.
        **kwargs : dict
            Arbitrary keyword arguments.

        Returns
        -------
        SQLite3ConnectionPool
            A singleton instance of the SQLite3ConnectionPool.
        """
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize(*args, **kwargs)
        return cls._instance

    def _initialize(
        self, path: str = constants.DEFAULT_DBFILE_PATH, min_size: int = 2, max_size: int = 10
    ) -> None:
        """
        Initialize the connection pool settings.

        Sets up the path, minimum size, and maximum size for the connection pool, and
        initializes the pool and its related tasks.

        Parameters
        ----------
        path : str, optional
            The file path to the SQLite3 database, by default constants.DEFAULT_DBFILE_PATH.
        min_size : int, optional
            The minimum number of connections to maintain in the pool, by default 2.
        max_size : int, optional
            The maximum number of connections in the pool, by default 10.
        """
        if not hasattr(self, "_initialized"):
            self._path = path
            self._min_size = min_size
            self._max_size = max_size
            self._pool: asyncio.Queue[SQLite3Connection] = asyncio.Queue(max_size)
            self._initialize_task: asyncio.Task | None = None
            self._initialized = False
            self._lock = asyncio.Lock()
            self._closing = False
            self._conn = None

    async def __aenter__(self) -> Connection:
        """
        Enter the runtime context and acquire a connection.

        Acquires a connection from the pool to be used within a context manager.

        Returns
        -------
        Connection
            An active database connection.

        Raises
        ------
        RuntimeError
            If the pool is in the process of closing.
        """
        if self._closing:
            msg = "Cannot acquire connection from a closing pool"
            raise RuntimeError(msg)
        self._conn = await self.acquire()
        return self._conn

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        """
        Exit the runtime context and release the connection.

        Releases the connection back to the pool when exiting a context manager.

        Parameters
        ----------
        exc_type : type
            The exception type.
        exc_value : Exception
            The exception instance.
        traceback : TracebackType
            The traceback object.
        """
        if self._conn is not None:
            await self.release(self._conn)

    async def _create_connection(self) -> SQLite3Connection:
        """
        Create a new SQLite3 connection.

        Establishes a new connection to the SQLite3 database.

        Returns
        -------
        Connection
            A new SQLite3 connection.

        Raises
        ------
        RuntimeError
            If an error occurs while creating the connection.
        """
        try:
            conn = SQLite3Connection(self._path)
            await conn.connect()
            return conn
        except Exception as e:
            log.error("Error creating connection: %s", e)
            msg = "Failed to create a connection"
            raise RuntimeError(msg) from e

    async def _initialize_pool(self) -> None:
        """
        Initialize the connection pool by creating the minimum number of connections.

        Creates the initial set of connections based on the minimum pool size and
        adds them to the pool.
        """
        tasks = [self._create_connection() for _ in range(self._min_size)]
        connections = await asyncio.gather(*tasks)
        for conn in connections:
            await self._pool.put(conn)
        log.debug("Connection pool initialized with %d connections.", self._min_size)
        self._initialized = True

    async def initialize(self) -> None:
        """
        Initialize the connection pool if it has not been initialized yet.

        Ensures the pool is initialized before any connections are acquired.

        Raises
        ------
        RuntimeError
            If the pool is in the process of closing.
        """
        if self._closing:
            msg = "Cannot initialize a closing pool"
            raise RuntimeError(msg)
        if not self._initialized and self._initialize_task is None:
            self._initialize_task = asyncio.create_task(self._initialize_pool())
            await self._initialize_task

    async def acquire(self) -> SQLite3Connection:
        """
        Acquire a connection from the pool.

        Returns an active database connection from the pool. If the pool has not been
        initialized, it will be initialized first.

        Returns
        -------
        SQLite3Connection
            An active database connection from the pool.

        Raises
        ------
        RuntimeError
            If the pool is in the process of closing.
        """
        if self._closing:
            msg = "Cannot acquire connection from a closing pool"
            raise RuntimeError(msg)
        await self.initialize()
        async with self._lock:
            if self._pool.empty() and self._pool.qsize() < self._max_size:
                return await self._create_connection()
            conn = await self._pool.get()
            if not conn.is_open:
                conn = await self._create_connection()
            log.debug("Connection acquired from the pool. Total available: %d", self._pool.qsize())
            return conn

    async def release(self, conn: SQLite3Connection) -> None:
        """
        Release a connection back to the pool.

        Returns a database connection back to the pool, making it available for reuse.
        If the connection is closed or the pool is full, it will be properly closed.

        Parameters
        ----------
        conn : SQLite3Connection
            The database connection to be released back into the pool.
        """
        if self._closing or not conn.is_open:
            await conn.close()
            return
        async with self._lock:
            if self._pool.qsize() < self._max_size:
                await self._pool.put(conn)
                log.debug(
                    "Connection released back to the pool. Total available: %d", self._pool.qsize()
                )
            else:
                await conn.close()

    async def close(self) -> None:
        """
        Close all connections in the pool.

        Ensures that all active connections in the pool are properly closed. This should
        be called when the pool is no longer needed.
        """
        self._closing = True
        while not self._pool.empty():
            conn = await self._pool.get()
            if conn.is_open:
                await conn.close()
        log.debug("All connections in the pool have been closed.")


sqlite_pool = SQLite3ConnectionPool()

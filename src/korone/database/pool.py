# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from typing import Protocol

from korone.database.connection import Connection


class ConnectionPool(Protocol):
    """
    Protocol for connection pools.

    Defines the necessary methods for managing a pool of database connections.
    """

    async def initialize(self) -> None:
        """
        Initialize the connection pool.

        This method sets up the initial pool of connections based on the minimum size.
        It should be called before any connections are acquired.
        """
        ...

    async def acquire(self) -> Connection:
        """
        Acquire a connection from the pool.

        Returns an active database connection from the pool. If the pool has not been
        initialized, it will be initialized first.

        Returns
        -------
        Connection
            An active database connection from the pool.
        """
        ...

    async def release(self, conn: Connection) -> None:
        """
        Release a connection back to the pool.

        Returns a database connection back to the pool, making it available for reuse.
        If the connection is closed or the pool is full, it will be properly closed.

        Parameters
        ----------
        conn : Connection
            The database connection to be released back into the pool.
        """
        ...

    async def close(self) -> None:
        """
        Close all connections in the pool.

        Ensures that all active connections in the pool are properly closed. This should
        be called when the pool is no longer needed.
        """
        ...

    async def __aenter__(self) -> Connection:
        """
        Enter the runtime context and acquire a connection.

        Acquires a connection from the pool to be used within a context manager.

        Returns
        -------
        Connection
            An active database connection.
        """
        ...

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
        ...

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>
# Copyright (c) 2023 Victor Cebarros <https://github.com/victorcebarros>

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol, Self, TypeVar

if TYPE_CHECKING:
    from types import TracebackType

    from .table import Table

T = TypeVar("T")


class Connection(Protocol):
    """Protocol defining the interface for database connections.

    This protocol establishes a common API for database connections, allowing
    different database engines to be used interchangeably with the same interface.
    """

    _path: str
    _args: tuple[Any, ...]
    _kwargs: dict[str, Any]
    _conn: Self | None = None

    async def __aenter__(self) -> Self:
        """Enter the async context manager.

        Returns:
            The connection instance
        """
        ...

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
        """
        ...

    async def is_open(self) -> bool:
        """Check if the database connection is open.

        Returns:
            True if the connection is open, False otherwise
        """
        ...

    async def commit(self) -> None:
        """Commit the current transaction."""
        ...

    async def connect(self) -> None:
        """Open a connection to the database."""
        ...

    async def execute(
        self, sql: str, parameters: tuple[Any, ...] = (), /, *, script: bool = False
    ) -> Any:
        """Execute an SQL statement or script.

        Args:
            sql: The SQL statement or script to execute
            parameters: The parameters to bind to the SQL statement
            script: If True, execute the SQL as a script with multiple statements

        Returns:
            The result of the SQL execution
        """
        ...

    async def table(self, name: str) -> Table:
        """Get a table interface for the given table name.

        Args:
            name: The name of the table

        Returns:
            A Table instance for the requested table
        """
        ...

    async def close(self) -> None:
        """Close the database connection."""
        ...

    async def vacuum(self) -> None:
        """Run database optimization to reduce file size and improve performance."""
        ...

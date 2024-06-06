# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>
# Copyright (c) 2023 Victor Cebarros <https://github.com/victorcebarros>

from typing import Optional, Protocol

from korone.database.table import Table


class Connection(Protocol):
    """
    Database connection.

    Connection Classes should receive the DBMS-specific
    parameters directly through the __init__ method.
    """

    _path: str
    _args: tuple
    _kwargs: dict
    _conn: Optional["Connection"] = None

    async def __aenter__(self) -> "Connection": ...

    async def __aexit__(self, exc_type, exc_value, traceback) -> None: ...

    async def is_open(self) -> bool:
        """
        Check if the connection is open.

        This method checks if the connection is open.

        Returns
        -------
        bool
            True if the connection is open, False otherwise.
        """
        ...

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
        ...

    async def connect(self) -> None:
        """
        Open a connection to a database.

        This method opens a connection to a database.
        """
        ...

    async def execute(self, sql: str, parameters: tuple = (), /) -> None:
        """
        Execute SQL operations.

        This method executes an SQL operation.

        Parameters
        ----------
        sql : str
            The SQL statement to be executed.
        parameters : tuple, optional
            The parameters to be used in the SQL statement, by default ().
        """
        ...

    async def table(self, name: str) -> Table:
        """
        Return a Table, which can be used for database related operations.

        This method returns a Table object, which can be used
        for database related operations.

        Parameters
        ----------
        name : str
            The name of the table.

        Returns
        -------
        Table
            A Table object representing the specified table.
        """
        ...

    async def close(self) -> None:
        """
        Close the connection.

        This method closes the connection to the database.
        """
        ...

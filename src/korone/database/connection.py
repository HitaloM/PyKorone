# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Victor Cebarros <https://github.com/victorcebarros>
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from typing import Protocol

from .table import Table


class Connection(Protocol):
    """
    Database connection.

    Connection Classes should receive the DBMS-specific
    parameters directly through the __init__ method.

    Examples
    --------
        >>> class SQLite3Connection:
        ...     # SQLite3-specific parameters are
        ...     # passed through __init__
        ...     def __init__(self, path: str):
        ...         self.path = path
        ...     # Context Manager
        ...     def __enter__(self):
        ...         ...
        ...         self.connect()
        ...     def __exit__(self):
        ...         ...
        ...         self.close()
        ...     def connect(self):
        ...         ...
        ...     def table(self, name: str) -> Table:
        ...         ...
        ...     def close(self):
        ...         ...
    """

    def __enter__(self):
        ...

    def __exit__(self, exc_type, exc_value, traceback):
        ...

    def connect(self):
        """
        Open a connection to a database.

        This method opens a connection to a database.
        """

    def execute(self, sql: str, parameters: tuple = (), /):
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

    def table(self, name: str) -> Table:
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

    def close(self):
        """
        Close the connection.

        This method closes the connection to the database.
        """

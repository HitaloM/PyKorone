# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Victor Cebarros <https://github.com/victorcebarros>
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

import sqlite3
from pathlib import Path
from typing import Any, Protocol

from korone.constants import DEFAULT_DBFILE_PATH
from korone.database.query import Query
from korone.database.table import Document, Documents, Table


class _Conn(Protocol):
    """
    Class with SQLite3-specific bits and pieces.

    This class is used internally by SQLite3Connection
    and SQLite3Table to perform operations on the
    database.

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

    _path: Path
    _args: tuple
    _kwargs: dict
    _conn: sqlite3.Connection | None = None

    def _is_open(self):
        """
        Check whether Database is open.

        This method checks whether the database is open
        or not. It returns True if the database is open,
        False otherwise.
        """

    def _execute(self, sql: str, parameters: tuple = (), /):
        """
        Execute SQL Command without checking whether self._conn is null or not.

        This method executes an SQL Command without checking
        whether self._conn is null or not. It returns the

        Parameters
        ----------
        sql : str
            The SQL statement to be executed.
        parameters : tuple, optional
            The parameters to be used in the SQL statement, by default ().
        """


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

    _conn: _Conn
    _table: str

    def __init__(self, *, conn: _Conn, table: str):
        if conn is None:
            raise RuntimeError("Connecton cannot be None")

        self._conn = conn
        self._table = table

    def insert(self, fields: Any | Document):
        """
        Insert a row on the table.

        This method inserts a row on the table.

        Parameters
        ----------
        fields : Any | Document
            The fields to be inserted.
        """
        if isinstance(fields, Document):
            values = tuple(fields.values())
        elif isinstance(fields, tuple | list):
            values = fields
        else:
            raise TypeError("Fields must be a Document, tuple, or list")

        placeholders = ", ".join(["?"] * len(values))

        sql = f"INSERT INTO {self._table} VALUES ({placeholders})"

        self._conn._execute(sql, tuple(values))

    def query(self, query: Query) -> Documents:
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

        rows = self._conn._execute(sql, data).fetchall()

        return [Document(row) for row in rows]

    def update(self, fields: Any | Document, query: Query):
        """
        Update fields on rows that match the criteria.

        This method updates the fields of rows that match
        the criteria specified by the query.

        Parameters
        ----------
        fields : Any | Document
            The fields to be updated.
        query : Query
            The query that specifies the criteria.
        """
        if isinstance(fields, Document):
            pairs = list(fields.items())
        elif isinstance(fields, tuple | list):
            pairs = fields
        else:
            raise TypeError("Fields must be a Document, tuple, or list")

        assignments = [f"{key} = ?" for key, value in pairs]

        assignments = ", ".join(assignments)

        values = [value for key, value in pairs]

        clause, data = query.compile()

        sql = f"UPDATE {self._table} SET {assignments} WHERE {clause}"

        self._conn._execute(sql, (*values, *data))

    def delete(self, query: Query):
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

        self._conn._execute(sql, data)


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

    _path: Path
    _args: tuple
    _kwargs: dict
    _conn: sqlite3.Connection | None = None

    def __init__(self, *args, path: Path = Path(DEFAULT_DBFILE_PATH), **kwargs):
        self._path: Path = path
        self._args = args
        self._kwargs = kwargs

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()

    def _is_open(self):
        return self._conn is not None

    def _execute(self, sql: str, parameters: tuple = (), /):
        # this method should only be called
        # internally, thereby we can afford to not check
        # its nullity
        conn: sqlite3.Connection = self._conn  # type: ignore

        # for readability, we shorten self._conn to conn
        with conn:
            return conn.execute(sql, parameters)

    def _executescript(self, sql: str):
        # this method should only be called
        # internally, thereby we can afford to not check
        # its nullity
        conn: sqlite3.Connection = self._conn  # type: ignore

        # for readability, we shorten self._conn to conn
        with conn:
            return conn.executescript(sql)

    def connect(self):
        """
        Connect to the SQLite database.

        This method connects to the SQLite database
        and stores the connection in the `_conn` attribute.

        Raises
        ------
        RuntimeError
            If the connection is already in place.
        """
        if self._is_open():
            raise RuntimeError("Connection is already in place.")

        self._conn = sqlite3.connect(
            self._path.expanduser().resolve(), *self._args, **self._kwargs
        )

    def table(self, name: str) -> Table:
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

    def execute(self, sql: str, parameters: tuple = (), /):
        """
        Execute an SQL statement with optional parameters.

        Executes an SQL statement with optional parameters.

        Parameters
        ----------
        sql : str
            The SQL statement to be executed.
        parameters : tuple, optional
            The parameters to be used in the SQL statement, by default ().

        Raises
        ------
        RuntimeError
            Raised if the connection is not yet open.
        """
        if not self._is_open():
            raise RuntimeError("Connection is not yet open.")

        self._execute(sql, parameters)

    def close(self):
        """
        Close the database connection.

        This method is automatically called when
        the context manager exits.

        Raises
        ------
        RuntimeError
            If the connection is not yet open.
        """
        if not self._is_open():
            raise RuntimeError("Connection is not yet open.")

        self._conn.close()

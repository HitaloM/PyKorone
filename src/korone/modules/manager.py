# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from abc import abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Generic, TypeVar

from korone.database.connection import Connection
from korone.database.impl import SQLite3Table
from korone.database.table import Document


class Table(Enum):
    """
    Enum class representing different tables.

    This class is used to identify the table to be used in the database.
    """

    USERS = auto()
    """The users table."""
    GROUPS = auto()
    """The groups table."""


class ChatColumn(Enum):
    """
    Enumeration representing columns in Users and Groups tables.

    This is used to identify the columns in the Users and Groups tables.
    """

    ID = auto()
    """The chat ID."""
    TYPE = auto()
    """The chat type."""
    LANGUAGE = auto()
    """The chat language."""
    REGISTRY_DATE = auto()
    """The chat registry date."""


@dataclass
class Chat:
    """
    Represents a chat.

    This dataclass is used to represent a chat in the database.
    """

    id: int
    """The chat ID.

    :type: int
    """
    type: str
    """The chat type.

    :type: str
    """
    language: str
    """The chat language.

    :type: str
    """
    registry_date: int
    """The chat registry date.

    :type: int
    """


T = TypeVar("T")


class Manager(SQLite3Table, Generic[T]):
    """
    A class representing a manager for a SQLite3 table.

    This class is used to manage a SQLite3 table, should
    be used as a base class for other managers.

    Parameters
    ----------
    conn : aiosqlite.Connection
        The connection to be used.
    table : Table
        The table to be used.

    Attributes
    ----------
    columns : dict[Enum, str]
        A dictionary mapping Enum values to column names.
    """

    def __init__(self, conn: Connection, table: Table) -> None:
        super().__init__(conn=conn, table=table.name.capitalize())

        self.columns: dict[Enum, str] = {}

    @abstractmethod
    def cast(self, fields: Document) -> T:
        """
        Cast the given fields into an object of type T.

        This method is used to cast the fields of a document into an object of type T.

        Parameters
        ----------
        fields : Document
            The fields to be casted.

        Returns
        -------
        T
            The casted object.
        """
        ...

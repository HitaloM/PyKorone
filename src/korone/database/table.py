# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Victor Cebarros <https://github.com/victorcebarros>
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from typing import Any, NewType, Protocol

from korone.database.query import Query


class Document(dict[str, Any]):
    """
    Document represents a single row on the SQL Database Table.

    One should note that, due to the limitation of Table
    Rows, one cannot use a Collection or Mapping as a
    Document Value.

    Examples
    --------
    >>> invaliddoc: Document = {"key": [1, 2, 3, 4, 5, 6]}
    """


Documents = NewType("Documents", list[Document])
"""
A list of Documents.
"""


class Table(Protocol):
    """
    Table from the database.

    It provides a higher level interface to the
    database by using queries, thereby preventing
    the user from dealing with SQL Queries directly.
    """

    async def insert(self, fields: Document) -> None:
        """
        Insert a row on the table.

        The `fields` parameter may be of any type that
        contains object.__dict__. It may also be a
        Document type.

        Keep in mind that, in the former case, keys
        starting with _ will be ignored, whereas in
        the latter, they will not.

        Parameters
        ----------
        fields : Document
            Fields to insert.

        Notes
        -----
        Document values *cannot* have nested values, due to the
        limitation of database rows. Refer to the Document type
        for more information.

        Examples
        --------
        >>> class HappyLittleCustomer:
        ...     def __init__(self, name: str):
        ...         self._name = name
        >>> gummikunde = HappyLittleCustomer("nibble")
        >>> vars(gummikunde)
        {'_name': 'nibble'}
        >>> # it won't insert anything, since we are passing
        >>> # a class instead of a Document
        >>> table.insert(gummikunde)
        """
        ...

    async def query(self, query: Query) -> Documents:
        """
        Query rows that match the criteria.

        This method will return a list of Documents, where each Document
        represents a row on the table.

        Parameters
        ----------
        query : Query
            Matching criteria.

        Returns
        -------
        Documents
            List of Documents of rows that matched the criteria.
        """
        ...

    async def update(self, fields: Document, query: Query) -> None:
        """
        Update fields on rows that match the criteria.

        The fields has a special behavior. You should check
        the method `insert` for more information.

        Parameters
        ----------
        fields : Document
            Fields to update.
        query : Query
            Matching criteria.
        """
        ...

    async def delete(self, query: Query) -> None:
        """
        Delete rows that match the criteria.

        This method will delete all rows that match the criteria.

        Parameters
        ----------
        query : Query
            Matching criteria.
        """
        ...

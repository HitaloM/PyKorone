# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023 Victor Cebarros <https://github.com/victorcebarros>
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from copy import copy
from typing import Any

# Represents a string containing placeholders for the
# data which will be bound on the SQL Statement.
# For example:
# >>> clause: Clause = "user == ?"
Clause = str

# Represents the actual data which is bound to a given
# placeholder.
# For example:
# >>> data: BoundData = ("Oliver",)
BoundData = tuple[Any, ...]

# Represents the result produced by a query, which
# is used internally to execute the appropriate SQL
# statement.
# For example:
# >>> result: CompiledQuery = ("user == ?", ("Oliver",))
CompiledQuery = tuple[Clause, BoundData]


class MalformedQueryError(Exception):
    """
    Malformed Query.

    This exception is raised when a query is malformed.
    """


class Query:
    """
    Queries allows you to specify what element or elements to fetch from the database.

    It provides a higher level interface to the database by using queries, thereby
    preventing the user from dealing with SQL Queries directly.

    Parameters
    ----------
    lhs : str, optional
        Left-hand side of the query.
    operator : str, optional
        Operator of the query.
    rhs : Any, optional
        Right-hand side of the query.

    Examples
    --------
    >>> # hypothetical, not yet implemented, connection class
    >>> conn = SQLite3Connection()
    >>> table = conn.table()
    >>> logician = Query()
    >>> table.query(logician.name == "Kazimierz Kuratowski")
    [{'desc': 'Polish mathematician and logician. [...]',
        'name': 'Kazimierz Kuratowski'}]
    """

    def __init__(self, *, lhs=None, operator=None, rhs=None) -> None:
        self.lhs = lhs
        self.operator = operator
        self.rhs = rhs

    def __getattr__(self, name: str) -> "Query":
        # Allows for instance.name
        self.lhs = name
        return self

    def __getitem__(self, item: str) -> "Query":
        # Allows for instance['name']
        return self.__getattr__(item)

    def __copy__(self) -> "Query":
        return Query(lhs=self.lhs, operator=self.operator, rhs=self.rhs)

    def __and__(self, other) -> "Query":
        return self._new_node(lhs=self, operator="AND", rhs=other)

    def __or__(self, other) -> "Query":
        return self._new_node(lhs=self, operator="OR", rhs=other)

    def __invert__(self) -> "Query":
        return self._new_node(operator="NOT", rhs=self)

    def __eq__(self, other) -> "Query":
        return self._new_node(lhs=self.lhs, operator="==", rhs=other)

    def __ne__(self, other) -> "Query":
        return self._new_node(lhs=self.lhs, operator="!=", rhs=other)

    def __lt__(self, other) -> "Query":
        return self._new_node(lhs=self.lhs, operator="<", rhs=other)

    def __le__(self, other) -> "Query":
        return self._new_node(lhs=self.lhs, operator="<=", rhs=other)

    def __gt__(self, other) -> "Query":
        return self._new_node(lhs=self.lhs, operator=">", rhs=other)

    def __ge__(self, other) -> "Query":
        return self._new_node(lhs=self.lhs, operator=">=", rhs=other)

    def _new_node(self, *, lhs=None, operator=None, rhs=None) -> "Query":
        query = Query(
            lhs=copy(lhs),
            operator=copy(operator),
            rhs=copy(rhs),
        )

        # consider this case, what should user by itself return?
        # >>> user = Query()
        # >>> (user.name == "Hyper Mega Chad Polyglot") & user
        # to keep a defined state, we clear previously defined keys
        self.lhs = None
        self.rhs = None

        return query

    def compile(self) -> CompiledQuery:
        """
        Compile a Query to SQL Clause and its Bound Data.

        This method will return a tuple containing the SQL Clause
        and the Bound Data, which is used internally to execute the
        appropriate SQL statement.

        Returns
        -------
        CompiledQuery
            A SQL Clause with Bound Data.
        """

        def isvalidoperator(obj: Any) -> bool:
            return isinstance(obj, str) and len(obj) != 0

        def visit(obj: Any) -> CompiledQuery:
            if not isinstance(obj, Query):
                raise MalformedQueryError("Cannot visit a non-query node.")

            if not isvalidoperator(obj.operator):
                raise MalformedQueryError("Invalid operator.")

            islhsquery = isinstance(obj.lhs, Query)
            isrhsquery = isinstance(obj.rhs, Query)

            if not islhsquery and not isrhsquery:
                if not isinstance(obj.lhs, str):
                    raise MalformedQueryError("Key must be a string.")
                return f"({obj.lhs} {obj.operator} ?)", (obj.rhs,)

            if islhsquery ^ isrhsquery:
                member: str = "Key"

                if isrhsquery:
                    member = "Value"

                raise MalformedQueryError(f"{member} cannot be a query type.")

            # *ph means PlaceHolder
            lhsstr, lhsph = visit(obj.lhs)
            rhsstr, rhsph = visit(obj.rhs)

            return f"({lhsstr} {obj.operator} {rhsstr})", (*lhsph, *rhsph)

        return visit(self)

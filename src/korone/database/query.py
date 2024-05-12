# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>
# Copyright (c) 2023 Victor Cebarros <https://github.com/victorcebarros>

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
    An exception raised when a query is not properly formed.

    This exception is raised when a query is not properly formed, such as when an invalid
    operator is used or when a key is not a string.
    """


class Query:
    """
    A class that provides a high-level interface for building SQL queries.

    This class allows you to specify what element or elements to fetch from the database.
    It provides a higher level interface to the database by using queries, thereby
    preventing the user from dealing with SQL Queries directly.

    The Query class uses operator overloading to build SQL queries. For example, the `==`
    operator is overloaded by the `__eq__` method to create a SQL equality condition. The `&`
    and `|` operators are overloaded to create SQL AND and OR conditions, respectively.

    The `__getattr__` and `__getitem__` methods are used to specify the column names in the SQL
    query. They set the left-hand side of the query condition.

    The `__copy__` method is used to create a copy of a Query instance. This is useful when you
    want to create a new query that is similar to an existing one.

    The `_new_node` method is used internally to create a new Query instance with the provided
    left-hand side, operator, and right-hand side. It is recommended to use this method
    instead of directly creating a Query instance to ensure a defined state.

    The `compile` method is used to compile the Query instance into a SQL clause and its
    bound data. It returns a tuple containing the SQL clause and the bound data, which is used
    internally to execute the appropriate SQL statement.

    Parameters
    ----------
    lhs : str, optional
        Left-hand side of the query.
    operator : str, optional
        Operator of the query.
    rhs : typing.Any, optional
        Right-hand side of the query.

    Examples
    --------
    >>> async with SQLite3Connection() as conn:
    ...     table = await conn.table("Users")
    ...     logician = Query()
    ...     await table.query(logician.name == "Kazimierz Kuratowski")
    [{'desc': 'Polish mathematician and logician. [...]',
        'name': 'Kazimierz Kuratowski'}]
    """

    __slots__ = ("lhs", "operator", "rhs")

    def __init__(self, *, lhs=None, operator=None, rhs=None) -> None:
        self.lhs = lhs
        self.operator = operator
        self.rhs = rhs

    def __getattr__(self, name: str) -> "Query":
        """
        Get an attribute of a Query instance.

        This method allows you to get an attribute of a Query instance. The returned Query object
        represents the updated Query instance with the attribute set. You can continue chaining
        operations on this returned Query object.

        Parameters
        ----------
        name : str
            Name of the attribute.

        Returns
        -------
        Query
            The Query instance with the attribute set.
        """
        self.lhs = name
        return self

    def __getitem__(self, item: str) -> "Query":
        """
        Get an item of a Query instance.

        This method allows you to get an item of a Query instance. The returned Query object
        represents the updated Query instance with the item set. You can continue chaining
        operations on this returned Query object.

        Parameters
        ----------
        item : str
            Name of the item.

        Returns
        -------
        Query
            The Query instance with the item set.
        """
        return self.__getattr__(item)

    def __copy__(self) -> "Query":
        """
        Create a copy of a Query instance.

        This method creates a new instance of the Query class that is a copy of the original
        Query instance. Modifying the copied Query object will not affect the original
        Query instance.

        Returns
        -------
        Query
            The copied Query instance.
        """
        return Query(lhs=self.lhs, operator=self.operator, rhs=self.rhs)

    def __and__(self, other) -> "Query":
        """
        Overload the & operator for the Query class.

        This method overloads the & operator for the Query class. The returned Query object
        represents a new Query instance with the AND operator applied between the original
        Query instance and the other Query instance.

        Parameters
        ----------
        other : Query
            The other Query instance.

        Returns
        -------
        Query
            The new Query instance with the AND operator.

        Examples
        --------
        >>> query = Query()
        >>> query.name == "John" & query.age == 20
        """
        return self._new_node(lhs=self, operator="AND", rhs=other)

    def __or__(self, other) -> "Query":
        """
        Overload the | operator for the Query class.

        This method overloads the | operator for the Query class. The returned Query object
        represents a new Query instance with the OR operator applied between the original
        Query instance and the other Query instance.

        Parameters
        ----------
        other : Query
            The other Query instance.

        Returns
        -------
        Query
            The new Query instance with the OR operator.

        Examples
        --------
        >>> query = Query()
        >>> query.name == "John" | query.age == 20
        """
        return self._new_node(lhs=self, operator="OR", rhs=other)

    def __invert__(self) -> "Query":
        """
        Overload the ~ operator for the Query class.

        This method overloads the ~ operator for the Query class. The returned Query object
        represents a new Query instance with the NOT operator applied to the original
        Query instance.

        Returns
        -------
        Query
            The new Query instance with the NOT operator.

        Examples
        --------
        >>> query = Query()
        >>> ~query.name == "John"
        """
        return self._new_node(operator="NOT", rhs=self)

    def __eq__(self, other) -> "Query":
        """
        Overload the == operator for the Query class.

        This method overloads the == operator for the Query class. The returned Query
        object represents a new Query instance with the equality operator applied between
        the original Query instance and the other Query instance.

        Parameters
        ----------
        other : Query
            The other Query instance.

        Returns
        -------
        Query
            The new Query instance with the == operator.

        Examples
        --------
        >>> query = Query()
        >>> query.name == "John"
        """
        return self._new_node(lhs=self.lhs, operator="==", rhs=other)

    def __ne__(self, other) -> "Query":
        """
        Overload the != operator for the Query class.

        The returned Query object represents a new Query instance with the not equals operator
        applied between the original Query instance and the other Query instance.

        Parameters
        ----------
        other : Query
            The other Query instance.

        Returns
        -------
        Query
            The new Query instance with the != operator.

        Examples
        --------
        >>> query = Query()
        >>> query.name != "John"
        """
        return self._new_node(lhs=self.lhs, operator="!=", rhs=other)

    def __lt__(self, other) -> "Query":
        """
        Overload the < operator for the Query class.

        This method overloads the < operator for the Query class. The returned Query
        object represents a new Query instance with the less than operator applied between
        the original Query instance and the other Query instance.

        Parameters
        ----------
        other : Query
            The other Query instance.

        Returns
        -------
        Query
            The new Query instance with the < operator.

        Examples
        --------
        >>> query = Query()
        >>> query.age < 20
        """
        return self._new_node(lhs=self.lhs, operator="<", rhs=other)

    def __le__(self, other) -> "Query":
        """
        Overload the <= operator for the Query class.

        The returned Query object represents a new Query instance with the less than or equal
        to operator applied between the original Query instance and the other Query instance.

        Parameters
        ----------
        other : Query
            The other Query instance.

        Returns
        -------
        Query
            The new Query instance with the <= operator.

        Examples
        --------
        >>> query = Query()
        >>> query.age <= 20
        """
        return self._new_node(lhs=self.lhs, operator="<=", rhs=other)

    def __gt__(self, other) -> "Query":
        """
        Overload the > operator for the Query class.

        The returned Query object represents a new Query instance with the greater than operator
        applied between the original Query instance and the other Query instance.

        Parameters
        ----------
        other : Query
            The other Query instance.

        Returns
        -------
        Query
            The new Query instance with the > operator.

        Examples
        --------
        >>> query = Query()
        >>> query.age > 20
        """
        return self._new_node(lhs=self.lhs, operator=">", rhs=other)

    def __ge__(self, other) -> "Query":
        """
        Overload the >= operator for the Query class.

        The returned Query object represents a new Query instance with the greater than or equal
        to operator applied between the original Query instance and the other Query instance.

        Parameters
        ----------
        other : Query
            The other Query instance.

        Returns
        -------
        Query
            The new Query instance with the >= operator.

        Examples
        --------
        >>> query = Query()
        >>> query.age >= 20
        """
        return self._new_node(lhs=self.lhs, operator=">=", rhs=other)

    def _new_node(self, *, lhs=None, operator=None, rhs=None) -> "Query":
        """
        Create a new Query instance.

        This method creates a new Query instance with the provided left-hand side, operator,
        and right-hand side. It is used internally to create new Query instances when
        overloading operators.

        Parameters
        ----------
        lhs : typing.Any, optional
            The left-hand side of the query expression, by default None.
        operator : typing.Any, optional
            The operator used in the query expression, by default None.
        rhs : typing.Any, optional
            The right-hand side of the query expression, by default None.

        Returns
        -------
        Query
            A new Query instance.

        Notes
        -----
        This method is used internally to create a new Query instance with the provided
        left-hand side, operator, and right-hand side. It is recommended to use this method
        instead of directly creating a Query instance to ensure a defined state.

        Examples
        --------
        >>> query = Query()
        >>> new_query = query._new_node(lhs="name", operator="==", rhs="John")
        >>> print(new_query)
        Query(lhs='name', operator='==', rhs='John')
        """
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

        Raises
        ------
        MalformedQueryError
            If the query is not properly formed.

        Examples
        --------
        >>> query = Query()
        >>> query.name == "John"
        >>> query.compile()
        ('name == ?', ('John',))
        """

        def isvalidoperator(obj: Any) -> bool:
            return isinstance(obj, str) and len(obj) != 0

        def visit(obj: Any) -> CompiledQuery:
            if not isinstance(obj, Query):
                msg = "Cannot visit a non-query node."
                raise MalformedQueryError(msg)

            if not isvalidoperator(obj.operator):
                msg = "Invalid operator."
                raise MalformedQueryError(msg)

            islhsquery = isinstance(obj.lhs, Query)
            isrhsquery = isinstance(obj.rhs, Query)

            if not islhsquery and not isrhsquery:
                if not isinstance(obj.lhs, str):
                    msg = "Key must be a string."
                    raise MalformedQueryError(msg)
                return f"({obj.lhs} {obj.operator} ?)", (obj.rhs,)

            if not islhsquery and isrhsquery:
                rhsstr, rhsph = visit(obj.rhs)
                return f"{obj.operator} {rhsstr}", (*rhsph,)

            if islhsquery ^ isrhsquery:
                member: str = "Key"

                if isrhsquery:
                    member = "Value"

                msg = f"{member} cannot be a query type."
                raise MalformedQueryError(msg)

            # *ph means PlaceHolder
            lhsstr, lhsph = visit(obj.lhs)
            rhsstr, rhsph = visit(obj.rhs)

            return f"({lhsstr} {obj.operator} {rhsstr})", (*lhsph, *rhsph)

        return visit(self)

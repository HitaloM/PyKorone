# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>
# Copyright (c) 2023 Victor Cebarros <https://github.com/victorcebarros>

from __future__ import annotations

from copy import copy
from typing import Any, Self

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
    """Exception raised when a query is malformed and cannot be compiled."""

    pass


class Query:
    """A query builder for SQL databases with a fluent interface.

    This class allows for building SQL queries programmatically using
    Python operators and method chaining. It supports logical operators
    like AND, OR, NOT, and comparison operators like ==, !=, <, <=, >, >=.

    Examples:
        >>> query = Query().user_id == 123
        >>> query = (Query().age >= 18) & (Query().age <= 65)
        >>> query = (Query().name == "John") | (Query().name == "Jane")

    Attributes:
        lhs: Left-hand side of the operation (usually a field name)
        operator: Operation to perform (e.g., "==", "!=", "AND", "OR")
        rhs: Right-hand side of the operation (usually a value or another query)
    """

    __slots__ = ("lhs", "operator", "rhs")

    def __init__(
        self, *, lhs: Any | None = None, operator: str | None = None, rhs: Any | None = None
    ) -> None:
        """Initialize a Query instance.

        Args:
            lhs: Left-hand side of the operation
            operator: Operation to perform
            rhs: Right-hand side of the operation
        """
        self.lhs: Any | None = lhs
        self.operator: str | None = operator
        self.rhs: Any | None = rhs

    def __getattr__(self, name: str) -> Self:
        """Get a field of the query by name.

        This method is called when accessing an attribute that doesn't exist,
        and it's used to build field references in the query.

        Args:
            name: The field name

        Returns:
            A new Query instance with the field name as the left-hand side

        Examples:
            >>> Query().user_id  # Creates a query with lhs="user_id"
        """
        self.lhs = name
        return self

    def __getitem__(self, item: str) -> Self:
        """Get a field of the query by dictionary-style access.

        This method allows for accessing fields with names that are not
        valid Python identifiers.

        Args:
            item: The field name

        Returns:
            A new Query instance with the field name as the left-hand side

        Examples:
            >>> Query()["user-id"]  # Creates a query with lhs="user-id"
        """
        return self.__getattr__(item)

    def __copy__(self) -> Self:
        """Create a shallow copy of the Query.

        Returns:
            A new Query instance with the same attributes
        """
        return self.__class__(lhs=self.lhs, operator=self.operator, rhs=self.rhs)

    def __and__(self, other: Self) -> Self:
        """Combine two queries with logical AND.

        Args:
            other: The query to combine with

        Returns:
            A new Query representing the AND combination

        Examples:
            >>> (Query().age >= 18) & (Query().age <= 65)
        """
        return self._new_node(lhs=self, operator="AND", rhs=other)

    def __or__(self, other: Self) -> Self:
        """Combine two queries with logical OR.

        Args:
            other: The query to combine with

        Returns:
            A new Query representing the OR combination

        Examples:
            >>> (Query().name == "John") | (Query().name == "Jane")
        """
        return self._new_node(lhs=self, operator="OR", rhs=other)

    def __invert__(self) -> Self:
        """Negate a query with logical NOT.

        Returns:
            A new Query representing the negation

        Examples:
            >>> ~(Query().is_active == True)
        """
        return self._new_node(operator="NOT", rhs=self)

    def __eq__(self, other: object) -> Self:
        """Create an equality comparison.

        Args:
            other: The value to compare with

        Returns:
            A new Query representing the equality comparison

        Examples:
            >>> Query().name == "John"
        """
        return self._new_node(lhs=self.lhs, operator="==", rhs=other)

    def __ne__(self, other: object) -> Self:
        """Create an inequality comparison.

        Args:
            other: The value to compare with

        Returns:
            A new Query representing the inequality comparison

        Examples:
            >>> Query().name != "John"
        """
        return self._new_node(lhs=self.lhs, operator="!=", rhs=other)

    def __lt__(self, other: Any) -> Self:
        """Create a less-than comparison.

        Args:
            other: The value to compare with

        Returns:
            A new Query representing the less-than comparison

        Examples:
            >>> Query().age < 18
        """
        return self._new_node(lhs=self.lhs, operator="<", rhs=other)

    def __le__(self, other: Any) -> Self:
        """Create a less-than-or-equal comparison.

        Args:
            other: The value to compare with

        Returns:
            A new Query representing the less-than-or-equal comparison

        Examples:
            >>> Query().age <= 18
        """
        return self._new_node(lhs=self.lhs, operator="<=", rhs=other)

    def __gt__(self, other: Any) -> Self:
        """Create a greater-than comparison.

        Args:
            other: The value to compare with

        Returns:
            A new Query representing the greater-than comparison

        Examples:
            >>> Query().age > 18
        """
        return self._new_node(lhs=self.lhs, operator=">", rhs=other)

    def __ge__(self, other: Any) -> Self:
        """Create a greater-than-or-equal comparison.

        Args:
            other: The value to compare with

        Returns:
            A new Query representing the greater-than-or-equal comparison

        Examples:
            >>> Query().age >= 18
        """
        return self._new_node(lhs=self.lhs, operator=">=", rhs=other)

    def _new_node(
        self, *, lhs: Any | None = None, operator: str | None = None, rhs: Any | None = None
    ) -> Self:
        """Create a new query node.

        Args:
            lhs: Left-hand side of the operation
            operator: Operation to perform
            rhs: Right-hand side of the operation

        Returns:
            A new Query instance with the specified attributes

        Notes:
            This method clears the current instance's lhs and rhs to prevent
            unexpected behavior in method chaining.
        """
        query = self.__class__(
            lhs=copy(lhs),
            operator=copy(operator),
            rhs=copy(rhs),
        )

        # Reset state to prevent issues with method chaining
        self.lhs = None
        self.rhs = None
        self.operator = None

        return query

    def compile(self) -> CompiledQuery:
        """Compile the query into a SQL clause and bound data.

        Returns:
            A tuple containing the SQL clause and the bound data

        Raises:
            MalformedQueryError: If the query is malformed

        Examples:
            >>> query = Query().name == "John"
            >>> query.compile()
            ("(name == ?)", ("John",))
        """

        def is_valid_operator(obj: Any) -> bool:
            """Check if an object is a valid operator.

            Args:
                obj: The object to check

            Returns:
                True if the object is a valid operator, False otherwise
            """
            return isinstance(obj, str) and bool(obj)

        def visit(obj: Any) -> CompiledQuery:
            """Visit a node in the query tree to compile it.

            Args:
                obj: The node to visit

            Returns:
                A tuple containing the SQL clause and bound data for the node

            Raises:
                MalformedQueryError: If the node is not a valid Query or has invalid attributes
            """
            if not isinstance(obj, Query):
                msg = "Cannot visit a non-query node."
                raise MalformedQueryError(msg)

            if not is_valid_operator(obj.operator):
                msg = "Invalid operator."
                raise MalformedQueryError(msg)

            is_lhs_query = isinstance(obj.lhs, Query)
            is_rhs_query = isinstance(obj.rhs, Query)

            # Case 1: Simple comparison between a field and a value
            if not is_lhs_query and not is_rhs_query:
                if not isinstance(obj.lhs, str):
                    msg = "Key must be a string."
                    raise MalformedQueryError(msg)
                return f"({obj.lhs} {obj.operator} ?)", (obj.rhs,)

            # Case 2: Unary operation (e.g. NOT)
            if not is_lhs_query and is_rhs_query:
                rhs_str, rhs_placeholders = visit(obj.rhs)
                return f"{obj.operator} {rhs_str}", (*rhs_placeholders,)

            # Case 3: Invalid query structure
            if is_lhs_query ^ is_rhs_query:
                member = "Key" if is_rhs_query else "Value"
                msg = f"{member} cannot be a query type."
                raise MalformedQueryError(msg)

            # Case 4: Binary operation between two queries (e.g. AND, OR)
            lhs_str, lhs_placeholders = visit(obj.lhs)
            rhs_str, rhs_placeholders = visit(obj.rhs)

            return f"({lhs_str} {obj.operator} {rhs_str})", (*lhs_placeholders, *rhs_placeholders)

        try:
            return visit(self)
        except MalformedQueryError:
            raise

    @classmethod
    def and_(cls, *queries: Self) -> Self:
        """Combine multiple queries with logical AND.

        Args:
            *queries: The queries to combine

        Returns:
            A new Query representing the AND combination of all queries

        Raises:
            ValueError: If no queries are provided

        Examples:
            >>> Query.and_(Query().age >= 18, Query().age <= 65, Query().is_active == True)
        """
        if not queries:
            msg = "At least one query is required"
            raise ValueError(msg)

        result = queries[0]
        for query in queries[1:]:
            result &= query

        return result

    @classmethod
    def or_(cls, *queries: Self) -> Self:
        """Combine multiple queries with logical OR.

        Args:
            *queries: The queries to combine

        Returns:
            A new Query representing the OR combination of all queries

        Raises:
            ValueError: If no queries are provided

        Examples:
            >>> Query.or_(Query().name == "John", Query().name == "Jane", Query().name == "Jack")
        """
        if not queries:
            msg = "At least one query is required"
            raise ValueError(msg)

        result = queries[0]
        for query in queries[1:]:
            result |= query

        return result

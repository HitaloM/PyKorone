# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>
# Copyright (c) 2023 Victor Cebarros <https://github.com/victorcebarros>

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
    pass


class Query:
    __slots__ = ("lhs", "operator", "rhs")

    def __init__(
        self, *, lhs: Any | None = None, operator: str | None = None, rhs: Any | None = None
    ) -> None:
        self.lhs: Any | None = lhs
        self.operator: str | None = operator
        self.rhs: Any | None = rhs

    def __getattr__(self, name: str) -> Self:
        self.lhs = name
        return self

    def __getitem__(self, item: str) -> Self:
        return self.__getattr__(item)

    def __copy__(self) -> Self:
        return self.__class__(lhs=self.lhs, operator=self.operator, rhs=self.rhs)

    def __and__(self, other: Self) -> Self:
        return self._new_node(lhs=self, operator="AND", rhs=other)

    def __or__(self, other: Self) -> Self:
        return self._new_node(lhs=self, operator="OR", rhs=other)

    def __invert__(self) -> Self:
        return self._new_node(operator="NOT", rhs=self)

    def __eq__(self, other: Any) -> Self:
        return self._new_node(lhs=self.lhs, operator="==", rhs=other)

    def __ne__(self, other: Any) -> Self:
        return self._new_node(lhs=self.lhs, operator="!=", rhs=other)

    def __lt__(self, other: Any) -> Self:
        return self._new_node(lhs=self.lhs, operator="<", rhs=other)

    def __le__(self, other: Any) -> Self:
        return self._new_node(lhs=self.lhs, operator="<=", rhs=other)

    def __gt__(self, other: Any) -> Self:
        return self._new_node(lhs=self.lhs, operator=">", rhs=other)

    def __ge__(self, other: Any) -> Self:
        return self._new_node(lhs=self.lhs, operator=">=", rhs=other)

    def _new_node(
        self, *, lhs: Any | None = None, operator: str | None = None, rhs: Any | None = None
    ) -> Self:
        query = self.__class__(
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

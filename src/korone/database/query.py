# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>
# Copyright (c) 2023 Victor Cebarros <https://github.com/victorcebarros>

from __future__ import annotations

from dataclasses import dataclass
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
    pass


@dataclass(slots=True)
class Query:
    lhs: str | Query | None = None
    operator: str | None = None
    rhs: Any | Query | None = None

    def __getattr__(self, name: str) -> Query:
        self.lhs = name
        return self

    def __getitem__(self, item: str) -> Query:
        return self.__getattr__(item)

    def __and__(self, other: Query) -> Query:
        return self._new_node(lhs=self, operator="AND", rhs=other)

    def __or__(self, other: Query) -> Query:
        return self._new_node(lhs=self, operator="OR", rhs=other)

    def __invert__(self) -> Query:
        return self._new_node(operator="NOT", rhs=self)

    def __eq__(self, other: Any) -> Query:
        return self._new_node(lhs=self.lhs, operator="==", rhs=other)

    def __ne__(self, other: Any) -> Query:
        return self._new_node(lhs=self.lhs, operator="!=", rhs=other)

    def __lt__(self, other: Any) -> Query:
        return self._new_node(lhs=self.lhs, operator="<", rhs=other)

    def __le__(self, other: Any) -> Query:
        return self._new_node(lhs=self.lhs, operator="<=", rhs=other)

    def __gt__(self, other: Any) -> Query:
        return self._new_node(lhs=self.lhs, operator=">", rhs=other)

    def __ge__(self, other: Any) -> Query:
        return self._new_node(lhs=self.lhs, operator=">=", rhs=other)

    def _new_node(
        self,
        *,
        lhs: str | Query | None = None,
        operator: str | None = None,
        rhs: Any | Query | None = None,
    ) -> Query:
        query = Query(lhs=lhs, operator=operator, rhs=rhs)

        # Clear previously defined keys to keep a defined state
        self.lhs = None
        self.rhs = None

        return query

    def compile(self) -> CompiledQuery:
        def isvalidoperator(obj: Any) -> bool:
            return isinstance(obj, str) and len(obj) != 0

        def visit(obj: Query) -> CompiledQuery:
            if not isinstance(obj, Query):
                msg = "Cannot visit a non-query node."
                raise MalformedQueryError(msg)

            if not isvalidoperator(obj.operator):
                msg = "Invalid operator."
                raise MalformedQueryError(msg)

            match (obj.lhs, obj.rhs):
                case (str(lhs), rhs) if not isinstance(rhs, Query):
                    return f"({lhs} {obj.operator} ?)", (rhs,)
                case (None, Query() as rhs):
                    rhsstr, rhsph = visit(rhs)
                    return f"{obj.operator} {rhsstr}", rhsph
                case (Query() as lhs, Query() as rhs):
                    lhsstr, lhsph = visit(lhs)
                    rhsstr, rhsph = visit(rhs)
                    return f"({lhsstr} {obj.operator} {rhsstr})", (*lhsph, *rhsph)
                case _:
                    msg = "Invalid query structure."
                    raise MalformedQueryError(msg)

        return visit(self)

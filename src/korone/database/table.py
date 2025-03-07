# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>
# Copyright (c) 2023 Victor Cebarros <https://github.com/victorcebarros>

from __future__ import annotations

from collections import UserDict
from typing import TYPE_CHECKING, Any, NewType, Protocol

if TYPE_CHECKING:
    from .query import Query


class Document(UserDict[str, Any]): ...


Documents = NewType("Documents", list[Document])


class Table(Protocol):
    async def insert(self, fields: Document) -> None: ...

    async def query(self, query: Query) -> Documents: ...

    async def update(self, fields: Document, query: Query) -> None: ...

    async def delete(self, query: Query) -> None: ...

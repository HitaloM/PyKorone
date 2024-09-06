# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>
# Copyright (c) 2023 Victor Cebarros <https://github.com/victorcebarros>

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from .table import Table


class Connection(Protocol):
    _path: str
    _args: tuple
    _kwargs: dict
    _conn: Connection | None = None

    async def __aenter__(self) -> Connection: ...

    async def __aexit__(self, exc_type, exc_value, traceback) -> None: ...

    async def is_open(self) -> bool: ...

    async def commit(self) -> None: ...

    async def connect(self) -> None: ...

    async def execute(self, sql: str, parameters: tuple = (), /) -> Any: ...

    async def table(self, name: str) -> Table: ...

    async def close(self) -> None: ...

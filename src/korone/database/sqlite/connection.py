# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>
# Copyright (c) 2023 Victor Cebarros <https://github.com/victorcebarros>

from pathlib import Path

import aiosqlite

from korone import constants
from korone.database.connection import Connection
from korone.database.sqlite.table import SQLite3Table
from korone.database.table import Table
from korone.utils.logging import logger


class SQLite3Connection(Connection):
    def __init__(self, path: str = constants.DEFAULT_DBFILE_PATH, *args, **kwargs) -> None:
        self._path = path
        self._args = args
        self._kwargs = kwargs
        self._conn: aiosqlite.Connection | None = None

    async def __aenter__(self) -> "SQLite3Connection":
        if not await self.is_open():
            await self.connect()
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        await self.close()

    async def is_open(self) -> bool:
        return self._conn is not None

    async def _execute(
        self, sql: str, parameters: tuple = (), /, script: bool = False
    ) -> aiosqlite.Cursor:
        if not self._conn:
            msg = "Connection is not open."
            raise RuntimeError(msg)

        logger.debug("Executing SQL: %s with parameters: %s", sql, parameters)

        return await (
            self._conn.executescript(sql) if script else self._conn.execute(sql, parameters)
        )

    async def commit(self) -> None:
        if not await self.is_open():
            msg = "Connection is not yet open."
            raise RuntimeError(msg)

        await self._conn.commit()  # type: ignore

    async def connect(self) -> None:
        if await self.is_open():
            msg = "Connection is already in place."
            raise RuntimeError(msg)

        if not Path(self._path).parent.exists():
            logger.info("Creating database directory")
            Path(self._path).parent.mkdir(parents=True, exist_ok=True)

        self._conn = await aiosqlite.connect(self._path, *self._args, **self._kwargs)
        await self._conn.execute("PRAGMA journal_mode=WAL;")

    async def table(self, name: str) -> Table:
        return SQLite3Table(conn=self, table=name)

    async def execute(
        self, sql: str, parameters: tuple = (), script: bool = False
    ) -> aiosqlite.Cursor:
        if not await self.is_open():
            msg = "Connection is not yet open."
            raise RuntimeError(msg)

        return await self._execute(sql, parameters, script)

    async def close(self) -> None:
        if not await self.is_open():
            msg = "Connection is not yet open."
            raise RuntimeError(msg)

        if self._conn:
            await self._conn.close()
            self._conn = None

    async def vacuum(self) -> None:
        if not await self.is_open():
            msg = "Connection is not yet open."
            raise RuntimeError(msg)

        logger.debug("Running VACUUM on the database.")
        if self._conn:
            await self._conn.execute("VACUUM;")
            await self._conn.commit()

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>
# Copyright (c) 2023 Victor Cebarros <https://github.com/victorcebarros>

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from korone.database.table import Document, Documents, Table

if TYPE_CHECKING:
    import aiosqlite

    from korone.database.connection import Connection
    from korone.database.query import Query


class SQLite3Table(Table):
    def __init__(self, conn: Connection, table: str) -> None:
        if conn is None:
            msg = "Connection cannot be None"
            raise RuntimeError(msg)

        self._conn = conn
        self._table = table

    async def _execute_and_commit(self, sql: str, params: tuple[Any, ...]) -> None:
        await self._conn.execute(sql, params)
        await self._conn.commit()

    async def insert(self, fields: Document) -> None:
        keys = ", ".join(key for key, value in fields.items() if value is not None)
        values = tuple(value for value in fields.values() if value is not None)
        placeholders = ", ".join("?" for _ in values)

        sql = f"INSERT OR IGNORE INTO {self._table} ({keys}) VALUES ({placeholders})"

        await self._execute_and_commit(sql, values)

    async def query(self, query: Query) -> Documents:
        clause, data = query.compile()
        sql = f"SELECT * FROM {self._table} WHERE {clause}"

        cursor: aiosqlite.Cursor = await self._conn.execute(sql, data)
        rows = await cursor.fetchall()

        documents = [
            Document({
                desc[0]: value for desc, value in zip(cursor.description, row, strict=False)
            })
            for row in rows
        ]

        return Documents(documents)

    async def update(self, fields: Document, query: Query) -> None:
        pairs = [(key, value) for key, value in fields.items() if value is not None]
        assignments = ", ".join(f"{key} = ?" for key, _ in pairs)
        values = [value for _, value in pairs]

        clause, data = query.compile()
        sql = f"UPDATE {self._table} SET {assignments} WHERE {clause}"

        await self._execute_and_commit(sql, (*values, *data))

    async def delete(self, query: Query) -> None:
        clause, data = query.compile()
        sql = f"DELETE FROM {self._table} WHERE {clause}"

        await self._execute_and_commit(sql, data)

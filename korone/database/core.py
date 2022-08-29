# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo M. <https://github.com/HitaloM>

import aiosqlite

from ..bot import Korone
from ..utils.logger import log


class Database(object):
    def __init__(self):
        self.conn: aiosqlite.Connection = None
        self.path: str = "./korone/database/db.sqlite"
        self.is_connected: bool = False

    async def connect(self):
        # Open the connection
        conn = await aiosqlite.connect(self.path)

        # Define the tables
        await conn.executescript(
            """
        CREATE TABLE IF NOT EXISTS users(
            id INTEGER PRIMARY KEY,
            language VARCHAR(2) NOT NULL DEFAULT \"en\",
            registration_time INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS chats(
            id INTEGER PRIMARY KEY,
            language VARCHAR(2) NOT NULL DEFAULT \"en\",
            registration_time INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS disabled(
            chat_id INTEGER,
            disabled_cmd TEXT
        );

        CREATE TABLE IF NOT EXISTS filters(
            chat_id INTEGER,
            handler TEXT,
            data TEXT,
            file_id TEXT,
            filter_type TEXT
        );

        CREATE TABLE IF NOT EXISTS afk(
            user_id INTEGER,
            reason TEXT,
            time INTEGER
        );
        """
        )

        # Enable VACUUM
        await conn.execute("VACUUM")

        # Enable WAL
        await conn.execute("PRAGMA journal_mode=WAL")

        # Update the database
        await conn.commit()

        conn.row_factory = aiosqlite.Row

        self.conn = conn
        self.is_connected: bool = True

        log.info(
            "[%s] The database has been connected.",
            Korone.__name__.lower(),
        )

    async def close(self):
        # Close the connection
        await self.conn.close()

        self.is_connected: bool = False

        log.info(
            "[%s] The database was closed.",
            Korone.__name__.lower(),
        )

    def get_conn(self) -> aiosqlite.Connection:
        if not self.is_connected:
            raise RuntimeError(
                "[%s] The database is not connected.",
                Korone.__name__.lower(),
            )

        return self.conn


database = Database()

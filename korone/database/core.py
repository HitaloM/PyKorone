# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

import logging

import aiosqlite

from korone.bot import Korone

logger = logging.getLogger(__name__)


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
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            language VARCHAR(2) NOT NULL DEFAULT \"en\",
            registration_time INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY,
            language VARCHAR(2) NOT NULL DEFAULT \"en\",
            registration_time INTEGER NOT NULL
        );

        CREATE TABLE IF NOT EXISTS disabled (
            chat_id INTEGER,
            disabled_cmd TEXT
        );

        CREATE TABLE IF NOT EXISTS filters(
            chat_id INTEGER ,
            handler TEXT,
            data TEXT,
            file_id TEXT,
            filter_type TEXT
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

        logger.info("[%s] The database has been connected.", Korone.__name__)

    async def close(self):
        # Close the connection
        await self.conn.close()

        self.is_connected: bool = False

        logger.info("[%s] The database was closed.", Korone.__name__)

    def get_conn(self) -> aiosqlite.Connection:
        if not self.is_connected:
            raise RuntimeError("The database is not connected.")

        return self.conn


database = Database()

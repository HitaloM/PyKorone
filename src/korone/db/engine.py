from typing import TYPE_CHECKING

from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine

from korone.config import CONFIG

if TYPE_CHECKING:
    import sqlite3

    from sqlalchemy.ext.asyncio import AsyncEngine
    from sqlalchemy.pool.base import ConnectionPoolEntry


def get_engine() -> AsyncEngine:
    engine = create_async_engine(url=CONFIG.db_url)

    @event.listens_for(engine.sync_engine, "connect")
    def _set_sqlite_pragmas(dbapi_connection: sqlite3.Connection, _connection_record: ConnectionPoolEntry) -> None:
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA journal_mode=WAL")
        result = cursor.fetchone()
        if result and result[0] != "wal":
            msg = f"Failed to set WAL mode, got: {result[0]}"
            raise RuntimeError(msg)

        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.execute("PRAGMA busy_timeout=5000")
        cursor.execute("PRAGMA wal_autocheckpoint=1000")
        cursor.close()

    return engine

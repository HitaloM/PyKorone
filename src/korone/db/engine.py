import sqlite3
from contextlib import suppress
from typing import TYPE_CHECKING

from sqlalchemy import event
from sqlalchemy.ext.asyncio import create_async_engine

from korone.config import CONFIG

if TYPE_CHECKING:
    from sqlalchemy.engine.interfaces import DBAPIConnection
    from sqlalchemy.ext.asyncio import AsyncEngine
    from sqlalchemy.pool import _ConnectionRecord

_engine_kwargs: dict[str, object] = {"echo": False, "future": True}

# SQLite pragmas below are tuned for a typical async Telegram bot workload:
# many short reads/writes, frequent concurrent coroutines, and low latency needs.
if CONFIG.db_url.startswith("sqlite"):
    _engine_kwargs.update({
        # Avoid hanging indefinitely on SQLITE_BUSY under concurrency.
        "connect_args": {"timeout": 30},
        # Helps detect stale pooled connections (cheap for SQLite).
        "pool_pre_ping": True,
    })

engine: AsyncEngine = create_async_engine(CONFIG.db_url, **_engine_kwargs)


@event.listens_for(engine.sync_engine, "connect")
def _configure_sqlite(dbapi_connection: DBAPIConnection, _connection_record: _ConnectionRecord) -> None:
    if engine.sync_engine.dialect.name != "sqlite":
        return

    cursor = dbapi_connection.cursor()

    pragmas: tuple[str, ...] = (
        "PRAGMA foreign_keys=ON",
        "PRAGMA journal_mode=WAL",
        "PRAGMA synchronous=NORMAL",
        "PRAGMA busy_timeout=5000",
        "PRAGMA temp_store=MEMORY",
        # Negative cache_size means KiB. Here: 64 MiB.
        "PRAGMA cache_size=-65536",
        # Keep WAL growth in check.
        "PRAGMA wal_autocheckpoint=1000",
        # Limit rollback/journal-related files (bytes).
        "PRAGMA journal_size_limit=67108864",
        # Optional, but can speed up reads on Linux when supported.
        "PRAGMA mmap_size=268435456",
    )

    for statement in pragmas:
        with suppress(sqlite3.Error):
            # SQLite/driver builds may not support all pragmas.
            # Best-effort: do not fail the whole connection for a tuning hint.
            cursor.execute(statement)

    cursor.close()

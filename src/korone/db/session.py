from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker

from korone.db.engine import engine

if TYPE_CHECKING:
    from collections.abc import AsyncIterator

    from sqlalchemy.ext.asyncio import AsyncSession

SessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(engine, expire_on_commit=False)


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    async with SessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def get_sqlite_stats() -> dict[str, int]:
    if engine.sync_engine.dialect.name != "sqlite":
        return {"page_count": 0, "page_size": 0, "db_size": 0}

    async with engine.begin() as conn:
        page_count = int((await conn.execute(text("PRAGMA page_count"))).scalar_one())
        page_size = int((await conn.execute(text("PRAGMA page_size"))).scalar_one())

    return {"page_count": page_count, "page_size": page_size, "db_size": page_count * page_size}


def _format_sqlite_synchronous(value: int) -> str:
    # https://www.sqlite.org/pragma.html#pragma_synchronous
    mapping = {0: "OFF", 1: "NORMAL", 2: "FULL", 3: "EXTRA"}
    return mapping.get(value, str(value))


async def get_sqlite_runtime_info() -> dict[str, str | int]:
    if engine.sync_engine.dialect.name != "sqlite":
        return {}

    async with engine.begin() as conn:
        journal_mode = str((await conn.execute(text("PRAGMA journal_mode"))).scalar_one())
        synchronous_raw = int((await conn.execute(text("PRAGMA synchronous"))).scalar_one())
        foreign_keys = int((await conn.execute(text("PRAGMA foreign_keys"))).scalar_one())
        busy_timeout = int((await conn.execute(text("PRAGMA busy_timeout"))).scalar_one())
        wal_autocheckpoint = int((await conn.execute(text("PRAGMA wal_autocheckpoint"))).scalar_one())
        cache_size = int((await conn.execute(text("PRAGMA cache_size"))).scalar_one())

    return {
        "journal_mode": journal_mode,
        "synchronous": _format_sqlite_synchronous(synchronous_raw),
        "foreign_keys": foreign_keys,
        "busy_timeout_ms": busy_timeout,
        "wal_autocheckpoint": wal_autocheckpoint,
        "cache_size": cache_size,
    }


async def dispose_engine() -> None:
    await engine.dispose()

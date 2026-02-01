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
        except Exception:
            await session.rollback()
            raise
        else:
            await session.commit()


async def get_sqlite_stats() -> dict[str, int]:
    if engine.sync_engine.dialect.name != "sqlite":
        return {"page_count": 0, "page_size": 0, "db_size": 0}

    async with engine.begin() as conn:
        page_count = (await conn.execute(text("PRAGMA page_count"))).scalar_one()
        page_size = (await conn.execute(text("PRAGMA page_size"))).scalar_one()
    db_size = int(page_count) * int(page_size)
    return {"page_count": int(page_count), "page_size": int(page_size), "db_size": db_size}


async def dispose_engine() -> None:
    await engine.dispose()

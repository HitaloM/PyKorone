from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from korone.db.engine import get_engine

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


@asynccontextmanager
async def session_scope() -> AsyncGenerator[AsyncSession]:
    engine = get_engine()
    async_session = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_sqlite_stats() -> dict[str, int]:
    async with session_scope() as session:
        page_count = (await session.execute(text("PRAGMA page_count"))).scalar_one_or_none() or 0
        page_size = (await session.execute(text("PRAGMA page_size"))).scalar_one_or_none() or 0
        db_size = int(page_count) * int(page_size)
        return {"page_count": int(page_count), "page_size": int(page_size), "db_size": int(db_size)}

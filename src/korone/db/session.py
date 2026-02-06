from contextlib import asynccontextmanager
from functools import lru_cache
from typing import TYPE_CHECKING

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from korone.db.engine import get_engine

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator


@lru_cache(maxsize=1)
def get_sessionmaker() -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(bind=get_engine(), class_=AsyncSession, expire_on_commit=False)


@asynccontextmanager
async def session_scope() -> AsyncGenerator[AsyncSession]:
    async_session = get_sessionmaker()

    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def get_postgres_stats() -> dict[str, int]:
    async with session_scope() as session:
        db_size = (await session.execute(text("SELECT pg_database_size(current_database())"))).scalar_one_or_none()
        return {"db_size": int(db_size or 0)}

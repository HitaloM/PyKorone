from functools import lru_cache
from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import create_async_engine

from korone.config import CONFIG

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine


@lru_cache(maxsize=1)
def get_engine() -> AsyncEngine:
    return create_async_engine(url=CONFIG.db_url, pool_pre_ping=True, pool_size=5, max_overflow=10, pool_timeout=30)

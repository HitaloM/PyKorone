from typing import TYPE_CHECKING

from sqlalchemy.ext.asyncio import create_async_engine

from korone.config import CONFIG

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncEngine


def get_engine() -> AsyncEngine:
    return create_async_engine(url=CONFIG.db_url)

from typing import TYPE_CHECKING, TypeVar

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.sql import ColumnElement

ModelT = TypeVar("ModelT", bound="Base")


class Base(AsyncAttrs, DeclarativeBase):
    pass


async def get_one[ModelT: "Base"](
    session: AsyncSession, model: type[ModelT], *filters: ColumnElement[bool]
) -> ModelT | None:
    stmt = select(model)
    if filters:
        stmt = stmt.where(*filters)
    result = await session.execute(stmt.limit(1))
    return result.scalars().first()

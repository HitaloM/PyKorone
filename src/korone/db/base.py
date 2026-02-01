from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Self, TypeVar

from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

from korone.db.session import SessionLocal

if TYPE_CHECKING:
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import Mapped
    from sqlalchemy.sql.elements import ColumnElement


class Base(AsyncAttrs, DeclarativeBase):
    pass


ModelT = TypeVar("ModelT", bound=Base)
type ColumnValue = (
    int
    | str
    | float
    | bool
    | datetime
    | Enum
    | list[str]
    | list[int]
    | dict[str, str | int | float | bool | None]
    | None
)


class AsyncModelMixin:
    id: Mapped[int]

    async def save(self) -> Self:
        async with SessionLocal() as session:
            async with session.begin():
                merged = await session.merge(self)
                await session.flush()
                return merged

    async def delete(self) -> None:
        async with SessionLocal() as session:
            async with session.begin():
                merged = await session.merge(self)
                await session.delete(merged)

    def to_dict(self) -> dict[str, ColumnValue]:
        mapper = inspect(self.__class__)
        data: dict[str, ColumnValue] = {}
        for column in mapper.columns:
            value = getattr(self, column.key)
            if value is not None:
                data[column.key] = value
        return data


async def get_one[ModelT: Base](
    session: AsyncSession, model: type[ModelT], *where: ColumnElement[bool]
) -> ModelT | None:
    stmt = select(model)
    if where:
        stmt = stmt.where(*where)
    result = await session.execute(stmt.limit(1))
    return result.scalar_one_or_none()


async def get_all[ModelT: Base](
    session: AsyncSession, model: type[ModelT], *where: ColumnElement[bool]
) -> list[ModelT]:
    stmt = select(model)
    if where:
        stmt = stmt.where(*where)
    result = await session.execute(stmt)
    return list(result.scalars().all())

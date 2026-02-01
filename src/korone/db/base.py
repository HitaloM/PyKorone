from datetime import datetime
from enum import Enum
from typing import TYPE_CHECKING, Any

from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase

if TYPE_CHECKING:
    from collections.abc import Sequence

    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy.orm import Mapped
    from sqlalchemy.sql.elements import ColumnElement

type ColumnValue = int | str | float | bool | datetime | Enum | list[Any] | dict[str, Any] | None


class Base(AsyncAttrs, DeclarativeBase):
    pass


class ModelMixin:
    id: Mapped[int]

    def to_dict(self) -> dict[str, ColumnValue]:
        return {col.key: val for col in inspect(self.__class__).columns if (val := getattr(self, col.key)) is not None}


async def get_one[T: Base](session: AsyncSession, model: type[T], *where: ColumnElement[bool]) -> T | None:
    stmt = select(model).where(*where) if where else select(model)
    return (await session.execute(stmt.limit(1))).scalar_one_or_none()


async def get_all[T: Base](session: AsyncSession, model: type[T], *where: ColumnElement[bool]) -> Sequence[T]:
    stmt = select(model).where(*where) if where else select(model)
    return (await session.execute(stmt)).scalars().all()

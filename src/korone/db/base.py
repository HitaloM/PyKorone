from typing import Any, Dict, Type, TypeVar

from sqlalchemy import inspect, select
from sqlalchemy.ext.asyncio import AsyncAttrs
from sqlalchemy.orm import DeclarativeBase, Mapped

from korone.db.session import SessionLocal


class Base(AsyncAttrs, DeclarativeBase):
    pass


ModelT = TypeVar("ModelT", bound=Base)


class AsyncModelMixin:
    id: Mapped[int]

    async def save(self):
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

    def to_dict(self) -> Dict[str, Any]:
        mapper = inspect(self.__class__)
        data: Dict[str, Any] = {}
        for column in mapper.columns:
            value = getattr(self, column.key)
            if value is not None:
                data[column.key] = value
        return data


async def get_one(session, model: Type[ModelT], *where) -> ModelT | None:
    stmt = select(model)
    if where:
        stmt = stmt.where(*where)
    result = await session.execute(stmt.limit(1))
    return result.scalar_one_or_none()


async def get_all(session, model: Type[ModelT], *where) -> list[ModelT]:
    stmt = select(model)
    if where:
        stmt = stmt.where(*where)
    result = await session.execute(stmt)
    return list(result.scalars().all())

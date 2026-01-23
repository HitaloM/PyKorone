from typing import Optional

from sqlalchemy import JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column

from korone.db.base import AsyncModelMixin, Base, get_one
from korone.db.db_exceptions import DBNotFoundException
from korone.db.session import session_scope


class DisablingModel(Base, AsyncModelMixin):
    __tablename__ = "disabled"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    cmds: Mapped[list[str]] = mapped_column(JSON, default=list)

    @staticmethod
    async def get_disabled(chat_id: int) -> list[str]:
        async with session_scope() as session:
            disabled = await get_one(session, DisablingModel, DisablingModel.chat_id == chat_id)

        if not disabled:
            return []

        return disabled.cmds or []

    @staticmethod
    async def disable(chat_id: int, cmd: str) -> "DisablingModel":
        async with session_scope() as session:
            model = await get_one(session, DisablingModel, DisablingModel.chat_id == chat_id)
            if not model:
                model = DisablingModel(chat_id=chat_id, cmds=[cmd])
                session.add(model)
                await session.flush()
                return model

            if cmd not in (model.cmds or []):
                model.cmds = [*model.cmds, cmd]
                session.add(model)
            return model

    @staticmethod
    async def enable(chat_id: int, cmd: str) -> "DisablingModel":
        async with session_scope() as session:
            model = await get_one(session, DisablingModel, DisablingModel.chat_id == chat_id)
            if not model or cmd not in (model.cmds or []):
                raise DBNotFoundException()

            model.cmds = [c for c in model.cmds if c != cmd]
            session.add(model)
            return model

    @staticmethod
    async def enable_all(chat_id: int) -> Optional["DisablingModel"]:
        async with session_scope() as session:
            model = await get_one(session, DisablingModel, DisablingModel.chat_id == chat_id)
            if model:
                await session.delete(model)
            return model

    @staticmethod
    async def set_disabled(chat_id: int, cmds: list[str]) -> "DisablingModel":
        async with session_scope() as session:
            model = await get_one(session, DisablingModel, DisablingModel.chat_id == chat_id)
            if not model:
                model = DisablingModel(chat_id=chat_id, cmds=cmds)
                session.add(model)
                await session.flush()
                return model

            model.cmds = cmds
            session.add(model)
            return model

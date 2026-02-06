from datetime import UTC, datetime

from sqlalchemy import func, select

from korone.db.base import get_one
from korone.db.models.lastfm import LastFMUserModel
from korone.db.session import session_scope


class LastFMRepository:
    @staticmethod
    async def total_count() -> int:
        async with session_scope() as session:
            result = await session.execute(select(func.count()).select_from(LastFMUserModel))
            return result.scalar_one() or 0

    @staticmethod
    async def get_username(chat_id: int) -> str | None:
        async with session_scope() as session:
            item = await get_one(session, LastFMUserModel, LastFMUserModel.chat_id == chat_id)
        return item.username if item else None

    @staticmethod
    async def set_username(chat_id: int, username: str) -> LastFMUserModel:
        async with session_scope() as session:
            if item := await get_one(session, LastFMUserModel, LastFMUserModel.chat_id == chat_id):
                item.username = username
                item.updated_at = datetime.now(UTC)
                return item

            item = LastFMUserModel(chat_id=chat_id, username=username)
            session.add(item)
            await session.flush()
            return item

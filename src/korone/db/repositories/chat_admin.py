from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from korone.db.base import get_one
from korone.db.models.chat_admin import ChatAdminModel
from korone.db.session import session_scope

if TYPE_CHECKING:
    from korone.db.models.chat import ChatModel


class ChatAdminRepository:
    @staticmethod
    async def get_chat_admin(chat: ChatModel, user: ChatModel) -> ChatAdminModel | None:
        async with session_scope() as session:
            return await get_one(
                session, ChatAdminModel, ChatAdminModel.chat_id == chat.id, ChatAdminModel.user_id == user.id
            )

    @staticmethod
    async def get_chat_admins(chat: ChatModel) -> list[ChatAdminModel]:
        async with session_scope() as session:
            stmt = select(ChatAdminModel).where(ChatAdminModel.chat_id == chat.id)
            result = await session.execute(stmt)
            return list(result.scalars().all())

    @staticmethod
    async def has_admins(chat: ChatModel) -> bool:
        async with session_scope() as session:
            stmt = select(ChatAdminModel.id).where(ChatAdminModel.chat_id == chat.id)
            result = await session.execute(stmt.limit(1))
            return result.scalar_one_or_none() is not None

    @staticmethod
    async def get_oldest_admin(chat: ChatModel) -> ChatAdminModel | None:
        async with session_scope() as session:
            stmt = select(ChatAdminModel).where(ChatAdminModel.chat_id == chat.id).order_by(ChatAdminModel.last_updated)
            return await session.scalar(stmt.limit(1))

    @staticmethod
    async def replace_chat_admins(chat: ChatModel, admins_map: dict[int, dict[str, Any]]) -> None:
        now = datetime.now(UTC)
        async with session_scope() as session:
            if admins_map:
                stmt = pg_insert(ChatAdminModel).values([
                    {"chat_id": chat.id, "user_id": user_id, "data": admin_data, "last_updated": now}
                    for user_id, admin_data in admins_map.items()
                ])
                await session.execute(
                    stmt.on_conflict_do_update(
                        index_elements=[ChatAdminModel.chat_id, ChatAdminModel.user_id],
                        set_={"data": stmt.excluded.data, "last_updated": now},
                    )
                )

            await session.execute(
                delete(ChatAdminModel).where(
                    ChatAdminModel.chat_id == chat.id, ChatAdminModel.user_id.not_in(tuple(admins_map))
                )
            )

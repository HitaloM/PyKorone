from __future__ import annotations

from datetime import UTC, datetime
from typing import TYPE_CHECKING, Any

from sqlalchemy import delete, select

from korone.db.models.chat_admin import ChatAdminModel
from korone.db.session import session_scope

if TYPE_CHECKING:
    from korone.db.models.chat import ChatModel


class ChatAdminRepository:
    @staticmethod
    async def get_chat_admin(chat: ChatModel, user: ChatModel) -> ChatAdminModel | None:
        async with session_scope() as session:
            stmt = select(ChatAdminModel).where(ChatAdminModel.chat_id == chat.id, ChatAdminModel.user_id == user.id)
            result = await session.execute(stmt.limit(1))
            return result.scalars().first()

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
            result = await session.execute(stmt.limit(1))
            return result.scalars().first()

    @staticmethod
    async def replace_chat_admins(chat: ChatModel, admins_map: dict[int, dict[str, Any]]) -> None:
        now = datetime.now(UTC)
        async with session_scope() as session:
            stmt = select(ChatAdminModel).where(ChatAdminModel.chat_id == chat.id)
            result = await session.execute(stmt)
            existing_admins = {model.user_id: model for model in result.scalars()}

            for user_id, admin_data in admins_map.items():
                if admin := existing_admins.get(user_id):
                    admin.data = admin_data
                    admin.last_updated = now
                    continue

                session.add(ChatAdminModel(chat_id=chat.id, user_id=user_id, data=admin_data, last_updated=now))

            stale_user_ids = set(existing_admins) - set(admins_map)
            if stale_user_ids:
                await session.execute(
                    delete(ChatAdminModel).where(
                        ChatAdminModel.chat_id == chat.id, ChatAdminModel.user_id.in_(stale_user_ids)
                    )
                )

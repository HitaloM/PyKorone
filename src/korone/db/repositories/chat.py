from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, TypedDict

from aiogram.enums import ChatType
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from korone.db.base import get_one
from korone.db.models.chat import ChatModel, ChatTopicModel, UserInGroupModel
from korone.db.session import session_scope

if TYPE_CHECKING:
    from aiogram.types import Chat, User


class ChatData(TypedDict):
    type: ChatType
    first_name_or_title: str
    last_name: str | None
    username: str | None
    is_bot: bool
    last_saw: datetime


class UserInGroupRepository:
    @staticmethod
    async def ensure_user_in_group(user: ChatModel, group: ChatModel) -> UserInGroupModel:
        now = datetime.now(UTC)
        async with session_scope() as session:
            stmt = (
                pg_insert(UserInGroupModel)
                .values(user_id=user.id, group_id=group.id, first_saw=now, last_saw=now)
                .on_conflict_do_update(
                    index_elements=[UserInGroupModel.user_id, UserInGroupModel.group_id], set_={"last_saw": now}
                )
                .returning(UserInGroupModel)
            )
            return (await session.scalars(stmt)).one()

    @staticmethod
    async def remove_user_in_chat(user_id: int, group_id: int) -> UserInGroupModel | None:
        async with session_scope() as session:
            if model := await get_one(
                session, UserInGroupModel, UserInGroupModel.user_id == user_id, UserInGroupModel.group_id == group_id
            ):
                await session.delete(model)
                return model
        return None

    @staticmethod
    async def delete_user_in_group(user_id: int, group: ChatModel) -> UserInGroupModel | None:
        if user := await ChatRepository.get_by_chat_id(user_id):
            return await UserInGroupRepository.remove_user_in_chat(user.id, group.id)
        return None

    @staticmethod
    async def get_user_in_group(user_id: int, group_id: int) -> UserInGroupModel | None:
        async with session_scope() as session:
            return await get_one(
                session, UserInGroupModel, UserInGroupModel.user_id == user_id, UserInGroupModel.group_id == group_id
            )

    @staticmethod
    async def count_user_groups(user_id: int) -> int:
        async with session_scope() as session:
            result = await session.execute(
                select(func.count()).select_from(UserInGroupModel).where(UserInGroupModel.user_id == user_id)
            )
            return result.scalar_one() or 0


class ChatTopicRepository:
    @staticmethod
    async def ensure_topic(group: ChatModel, thread_id: int, topic_name: str | None) -> ChatTopicModel:
        now = datetime.now(UTC)
        async with session_scope() as session:
            stmt = pg_insert(ChatTopicModel).values(
                group_id=group.id, thread_id=thread_id, name=topic_name, last_active=now
            )
            stmt = stmt.on_conflict_do_update(
                index_elements=[ChatTopicModel.group_id, ChatTopicModel.thread_id],
                set_={"name": func.coalesce(func.nullif(stmt.excluded.name, ""), ChatTopicModel.name)},
            ).returning(ChatTopicModel)
            return (await session.scalars(stmt)).one()


class ChatRepository:
    @staticmethod
    def _user_data(user: User) -> ChatData:
        return {
            "type": ChatType.PRIVATE,
            "first_name_or_title": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "is_bot": user.is_bot,
            "last_saw": datetime.now(UTC),
        }

    @staticmethod
    def _group_data(chat: Chat) -> ChatData:
        return {
            "type": ChatType(chat.type),
            "first_name_or_title": chat.title or "Group",
            "last_name": None,
            "username": chat.username,
            "is_bot": False,
            "last_saw": datetime.now(UTC),
        }

    @classmethod
    async def upsert_user(cls, user: User) -> ChatModel:
        return await cls._upsert(user.id, cls._user_data(user))

    @classmethod
    async def upsert_group(cls, chat: Chat) -> ChatModel:
        return await cls._upsert(chat.id, cls._group_data(chat))

    @classmethod
    async def _upsert(cls, chat_id: int, data: ChatData) -> ChatModel:
        async with session_scope() as session:
            stmt = (
                pg_insert(ChatModel)
                .values(chat_id=chat_id, **data)
                .on_conflict_do_update(index_elements=[ChatModel.chat_id], set_=dict(data))
                .returning(ChatModel)
            )
            return (await session.scalars(stmt)).one()

    @staticmethod
    async def do_chat_migrate(old_id: int, new_chat: Chat) -> ChatModel | None:
        async with session_scope() as session:
            if chat := await get_one(session, ChatModel, ChatModel.chat_id == old_id):
                chat.chat_id = new_chat.id
                chat.type = ChatType(new_chat.type)
                return chat
        return None

    @staticmethod
    async def total_count(chat_types: tuple[ChatType, ...]) -> int:
        async with session_scope() as session:
            result = await session.execute(select(func.count()).where(ChatModel.type.in_(chat_types)))
            return result.scalar_one() or 0

    @staticmethod
    async def new_count_last_48h(chat_types: tuple[ChatType, ...]) -> int:
        threshold = datetime.now(UTC) - timedelta(hours=48)
        async with session_scope() as session:
            result = await session.execute(
                select(func.count()).where(
                    ChatModel.last_saw >= threshold, ChatModel.first_saw >= threshold, ChatModel.type.in_(chat_types)
                )
            )
            return result.scalar_one() or 0

    @staticmethod
    async def active_count_last_48h(chat_types: tuple[ChatType, ...]) -> int:
        threshold = datetime.now(UTC) - timedelta(hours=48)
        async with session_scope() as session:
            result = await session.execute(
                select(func.count()).where(
                    ChatModel.last_saw >= threshold, ChatModel.first_saw <= threshold, ChatModel.type.in_(chat_types)
                )
            )
            return result.scalar_one() or 0

    @staticmethod
    async def delete_chat(chat: ChatModel) -> None:
        async with session_scope() as session:
            merged = await session.merge(chat)
            await session.delete(merged)

    @staticmethod
    async def get_by_chat_id(chat_id: int) -> ChatModel | None:
        async with session_scope() as session:
            return await get_one(session, ChatModel, ChatModel.chat_id == chat_id)

    @staticmethod
    async def get_by_id(pk: int) -> ChatModel | None:
        async with session_scope() as session:
            return await get_one(session, ChatModel, ChatModel.id == pk)

    @staticmethod
    async def find_user(user_id: int) -> ChatModel:
        async with session_scope() as session:
            if user := await get_one(
                session, ChatModel, ChatModel.chat_id == user_id, ChatModel.type == ChatType.PRIVATE
            ):
                return user
        msg = "User not found"
        raise LookupError(msg)

    @staticmethod
    async def find_user_by_username(username: str) -> ChatModel:
        async with session_scope() as session:
            if user := await get_one(session, ChatModel, ChatModel.username == username):
                return user
        msg = "User not found"
        raise LookupError(msg)

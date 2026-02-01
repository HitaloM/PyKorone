from datetime import UTC, datetime, timedelta  # noqa: I001
from enum import Enum
from typing import TYPE_CHECKING

from anyio import Lock
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func, select
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import mapped_column, relationship, Mapped  # noqa: TC002

from korone.db.base import AsyncModelMixin, Base, get_one
from korone.db.db_exceptions import DBNotFoundException
from korone.db.session import session_scope

if TYPE_CHECKING:
    from aiogram.types import Chat, User

type ChatDataValue = ChatType | str | bool | datetime | None
type ChatData = dict[str, ChatDataValue]


class ChatType(Enum):
    group = "group"
    supergroup = "supergroup"
    private = "private"


class UserInGroupModel(Base, AsyncModelMixin):
    __tablename__ = "users_in_groups"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), index=True)
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), index=True)
    first_saw: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    last_saw: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    user: Mapped[ChatModel] = relationship("ChatModel", foreign_keys=[user_id])
    group: Mapped[ChatModel] = relationship("ChatModel", foreign_keys=[group_id])

    @staticmethod
    async def ensure_user_in_group(user: ChatModel, group: ChatModel) -> UserInGroupModel:
        current_timedate = datetime.now(UTC)

        async with session_scope() as session:
            model = await get_one(
                session, UserInGroupModel, UserInGroupModel.user_id == user.id, UserInGroupModel.group_id == group.id
            )
            if model:
                model.last_saw = current_timedate
                session.add(model)
                return model

            model = UserInGroupModel(user_id=user.id, group_id=group.id, last_saw=current_timedate)
            session.add(model)
            await session.flush()
            return model

    @staticmethod
    async def remove_user_in_chat(user_id: int, group_id: int) -> UserInGroupModel | None:
        async with session_scope() as session:
            user_in_chat = await get_one(
                session, UserInGroupModel, UserInGroupModel.user_id == user_id, UserInGroupModel.group_id == group_id
            )
            if user_in_chat:
                await session.delete(user_in_chat)
            return user_in_chat

    @staticmethod
    async def ensure_delete(user: ChatModel, group: ChatModel) -> UserInGroupModel | None:
        async with session_scope() as session:
            user_in_chat = await get_one(
                session, UserInGroupModel, UserInGroupModel.user_id == user.id, UserInGroupModel.group_id == group.id
            )
            if user_in_chat:
                await session.delete(user_in_chat)
                return user_in_chat
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


class ChatTopicModel(Base, AsyncModelMixin):
    __tablename__ = "chat_topics"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    group_id: Mapped[int] = mapped_column(Integer, ForeignKey("chats.id", ondelete="CASCADE"), index=True)
    thread_id: Mapped[int] = mapped_column(Integer, index=True)
    name: Mapped[str | None] = mapped_column(String(128), nullable=True)
    last_active: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    group: Mapped[ChatModel] = relationship("ChatModel", foreign_keys=[group_id])

    @staticmethod
    async def ensure_topic(group: ChatModel, thread_id: int, topic_name: str | None) -> ChatTopicModel:
        async with session_scope() as session:
            model = await get_one(
                session, ChatTopicModel, ChatTopicModel.group_id == group.id, ChatTopicModel.thread_id == thread_id
            )
            if not model:
                model = ChatTopicModel(group_id=group.id, thread_id=thread_id, name=topic_name)
                session.add(model)
                await session.flush()
                return model

            if (topic_name and topic_name != model.name) or (topic_name and not model.name):
                model.name = topic_name
                session.add(model)
            return model


class ChatModel(Base, AsyncModelMixin):
    __tablename__ = "chats"

    _upsert_lock = Lock()

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(Integer, unique=True, index=True)
    type: Mapped[ChatType] = mapped_column(SAEnum(ChatType), index=True)
    first_name_or_title: Mapped[str] = mapped_column(String(128))
    last_name: Mapped[str | None] = mapped_column(String(64), nullable=True)
    username: Mapped[str | None] = mapped_column(String(64), nullable=True, index=True)
    is_bot: Mapped[bool] = mapped_column(Boolean, default=False)
    first_saw: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))
    last_saw: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(UTC))

    @staticmethod
    def _get_user_data(user: User) -> ChatData:
        return {
            "type": ChatType.private,
            "first_name_or_title": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "is_bot": user.is_bot,
            "last_saw": datetime.now(UTC),
        }

    @staticmethod
    def _get_group_data(chat: Chat) -> ChatData:
        return {
            "type": ChatType[chat.type],
            "first_name_or_title": chat.title,
            "last_name": None,
            "username": chat.username,
            "is_bot": False,
            "last_saw": datetime.now(UTC),
        }

    @property
    def tid(self) -> int:
        return self.chat_id

    @staticmethod
    def get_user_model(user: User) -> ChatModel:
        return ChatModel(chat_id=user.id, **ChatModel._get_user_data(user))

    @staticmethod
    def get_group_model(chat: Chat) -> ChatModel:
        return ChatModel(chat_id=chat.id, **ChatModel._get_group_data(chat))

    @staticmethod
    async def upsert_user(user: User) -> ChatModel:
        data = ChatModel._get_user_data(user)
        return await ChatModel._upsert(user.id, data)

    @staticmethod
    async def upsert_group(chat: Chat) -> ChatModel:
        data = ChatModel._get_group_data(chat)
        return await ChatModel._upsert(chat.id, data)

    @staticmethod
    async def _upsert(chat_id: int, data: ChatData) -> ChatModel:
        async with ChatModel._upsert_lock:
            async with session_scope() as session:
                model = await get_one(session, ChatModel, ChatModel.chat_id == chat_id)
                if model:
                    for key, value in data.items():
                        setattr(model, key, value)
                    session.add(model)
                    return model

                model = ChatModel(chat_id=chat_id, **data)
                session.add(model)
                await session.flush()
                return model

    @staticmethod
    async def do_chat_migrate(old_id: int, new_chat: Chat) -> ChatModel | None:
        async with session_scope() as session:
            chat = await get_one(session, ChatModel, ChatModel.chat_id == old_id)
            if chat:
                chat.chat_id = new_chat.id
                chat.type = ChatType[new_chat.type]
                session.add(chat)
            return chat

    @staticmethod
    async def total_count(chat_types: tuple[ChatType, ...]) -> int:
        async with session_scope() as session:
            result = await session.execute(select(func.count()).where(ChatModel.type.in_(chat_types)))
            return int(result.scalar_one())

    @staticmethod
    async def new_count_last_48h(chat_types: tuple[ChatType, ...]) -> int:
        threshold = datetime.now(UTC) - timedelta(hours=48)
        async with session_scope() as session:
            result = await session.execute(
                select(func.count()).where(
                    ChatModel.last_saw >= threshold, ChatModel.first_saw >= threshold, ChatModel.type.in_(chat_types)
                )
            )
            return int(result.scalar_one())

    @staticmethod
    async def active_count_last_48h(chat_types: tuple[ChatType, ...]) -> int:
        threshold = datetime.now(UTC) - timedelta(hours=48)
        async with session_scope() as session:
            result = await session.execute(
                select(func.count()).where(
                    ChatModel.last_saw >= threshold, ChatModel.first_saw <= threshold, ChatModel.type.in_(chat_types)
                )
            )
            return int(result.scalar_one())

    async def delete_chat(self) -> None:
        await self.delete()

    @staticmethod
    async def get_by_chat_id(chat_id: int) -> ChatModel | None:
        async with session_scope() as session:
            return await get_one(session, ChatModel, ChatModel.chat_id == chat_id)

    @staticmethod
    async def get_by_tid(chat_id: int) -> ChatModel | None:
        return await ChatModel.get_by_chat_id(chat_id)

    @staticmethod
    async def get_by_id(id: int) -> ChatModel | None:
        async with session_scope() as session:
            return await get_one(session, ChatModel, ChatModel.id == id)

    @staticmethod
    async def find_user(user_id: int) -> ChatModel:
        async with session_scope() as session:
            user = await get_one(session, ChatModel, ChatModel.chat_id == user_id, ChatModel.type == ChatType.private)

        if not user:
            raise DBNotFoundException()

        return user

    @staticmethod
    async def find_user_by_username(username: str) -> ChatModel:
        async with session_scope() as session:
            user = await get_one(session, ChatModel, ChatModel.username == username)
        if not user:
            raise DBNotFoundException()

        return user

    @staticmethod
    def user_from_id(user_id: int) -> ChatModel:
        return ChatModel(
            chat_id=user_id,
            first_name_or_title="User",
            is_bot=False,
            username=None,
            type=ChatType.private,
            last_saw=datetime.now(UTC),
        )

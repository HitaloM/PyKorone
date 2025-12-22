from asyncio import Lock
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Annotated, Any, Optional

from aiogram.types import Chat, User
from beanie import (
    DeleteRules,
    Document,
    Indexed,
    PydanticObjectId,
    UpdateResponse,
)
from beanie.odm.operators.find.comparison import In
from beanie.odm.operators.update.general import Set
from pydantic import Field
from pydantic_core.core_schema import SerializerFunctionWrapHandler
from pymongo import IndexModel

from sophie_bot.db.db_exceptions import DBNotFoundException
from sophie_bot.db.models._link_type import Link


class ChatType(Enum):
    group = "group"
    supergroup = "supergroup"
    private = "private"
    channel = "channel"


class UserInGroupModel(Document):
    user: Link["ChatModel"]
    group: Link["ChatModel"]
    first_saw: datetime = Field(default_factory=datetime.utcnow)
    last_saw: datetime

    class Settings:
        name = "users_in_groups"
        indexes = [
            IndexModel(("user.$id", "group.$id"), unique=False),  # TODO: Should be unique but has duplicates
        ]

    @staticmethod
    async def ensure_user_in_group(user: "ChatModel", group: "ChatModel"):
        current_timedate = datetime.now(timezone.utc)

        return await UserInGroupModel.find_one(
            UserInGroupModel.user.id == user.id,
            UserInGroupModel.group.id == group.id,
        ).upsert(
            Set({UserInGroupModel.last_saw: current_timedate}),
            on_insert=UserInGroupModel(
                user=user,
                group=group,
                last_saw=current_timedate,
            ),
        )

    @staticmethod
    async def remove_user_in_chat(user_iid: PydanticObjectId, group_iid: PydanticObjectId):
        user_in_chat = await UserInGroupModel.find_one(
            UserInGroupModel.user.id == user_iid, UserInGroupModel.group.id == group_iid
        )
        if user_in_chat:
            await user_in_chat.delete()
        return user_in_chat

    @staticmethod
    async def ensure_delete(user: "ChatModel", group: "ChatModel") -> Optional["UserInGroupModel"]:
        if user_in_chat := await UserInGroupModel.find_one(
            UserInGroupModel.user.id == user.id, UserInGroupModel.group.id == group.id
        ):
            await user_in_chat.delete()
            return user_in_chat
        return None

    @staticmethod
    async def get_user_in_group(
        user_iid: PydanticObjectId, group_iid: PydanticObjectId
    ) -> Optional["UserInGroupModel"]:
        return await UserInGroupModel.find_one(
            UserInGroupModel.user.id == user_iid, UserInGroupModel.group.id == group_iid
        )


class ChatTopicModel(Document):
    group: Link["ChatModel"]
    thread_id: int
    name: Optional[str] = None
    last_active: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "chat_topics"

    @staticmethod
    async def ensure_topic(group: "ChatModel", thread_id: int, topic_name: Optional[str]):
        model: Optional[ChatTopicModel] = await ChatTopicModel.find_one(
            ChatTopicModel.group.id == group.id, ChatTopicModel.thread_id == thread_id
        )

        if not model:
            model = ChatTopicModel(group=group, thread_id=thread_id, name=topic_name)
            await model.save()
            return model

        if (topic_name and topic_name != model.name) or (topic_name and not model.name):
            model.name = topic_name
            await model.save()

        return model


def ser_wrap(v: Any, nxt: SerializerFunctionWrapHandler) -> str:
    return nxt(v)


class ChatModel(Document):
    id: PydanticObjectId = Field(default_factory=PydanticObjectId, alias="_id")
    chat_id: Annotated[int, Indexed(unique=True)]
    type: ChatType = Field(..., description="Group type")
    first_name_or_title: str = Field(max_length=128)
    last_name: Optional[str] = Field(max_length=64, default=None)
    username: Annotated[Optional[str], Indexed()]
    is_bot: bool

    first_saw: datetime = Field(default_factory=datetime.utcnow)
    last_saw: datetime

    # User in groups
    # user_in_groups: list[BackLink[UserInGroupModel]] = Field(original_field="user")  # type: ignore[call-arg]
    # groups_of_user: list[BackLink[UserInGroupModel]] = Field(original_field="group")  # type: ignore[call-arg]

    # Topics
    # chat_topics: list[BackLink[ChatTopicModel]] = Field(original_field="group")  # type: ignore[call-arg]

    # AI
    # ai_enabled: list[BackLink[AIEnabledModel]] = Field(original_field="chat")  # type: ignore[call-arg]
    # ai_usage: list[BackLink[AIUsageModel]] = Field(original_field="chat")  # type: ignore[call-arg]

    class Settings:
        name = "chats"
        max_nesting_depth = 2

    @staticmethod
    def _get_user_data(user: User) -> dict[str, Any]:
        return {
            "type": ChatType.private,
            "first_name_or_title": user.first_name,
            "last_name": user.last_name,
            "username": user.username,
            "is_bot": user.is_bot,
            "last_saw": datetime.now(timezone.utc),
        }

    @staticmethod
    def _get_group_data(chat: Chat) -> dict[str, Any]:
        return {
            "type": ChatType[chat.type],
            "first_name_or_title": chat.title,
            "last_name": None,
            "username": chat.username,
            "is_bot": False,
            "last_saw": datetime.now(timezone.utc),
        }

    @staticmethod
    def get_user_model(user: User) -> "ChatModel":
        return ChatModel(chat_id=user.id, **ChatModel._get_user_data(user))

    @staticmethod
    def get_group_model(chat: Chat) -> "ChatModel":
        return ChatModel(chat_id=chat.id, **ChatModel._get_group_data(chat))

    @staticmethod
    async def upsert_user(user: User) -> "ChatModel":
        async with Lock():
            data = ChatModel._get_user_data(user)
            return await ChatModel.find_one(ChatModel.chat_id == user.id).upsert(
                Set(data), on_insert=ChatModel(chat_id=user.id, **data), response_type=UpdateResponse.NEW_DOCUMENT
            )

    @staticmethod
    async def upsert_group(chat: Chat) -> "ChatModel":
        async with Lock():
            data = ChatModel._get_group_data(chat)

            return await ChatModel.find_one(ChatModel.chat_id == chat.id).upsert(
                Set(data), on_insert=ChatModel(chat_id=chat.id, **data), response_type=UpdateResponse.NEW_DOCUMENT
            )

    @staticmethod
    async def do_chat_migrate(old_id: int, new_chat: Chat) -> Optional["ChatModel"]:
        chat = await ChatModel.find_one(ChatModel.chat_id == old_id)
        if chat:
            chat.chat_id = new_chat.id
            chat.type = ChatType[new_chat.type]
            await chat.save()
        return chat

    @staticmethod
    async def total_count(chat_types: tuple[ChatType, ...]) -> int:
        return await ChatModel.find(In(ChatModel.type, chat_types)).count()

    @staticmethod
    async def new_count_last_48h(chat_types: tuple[ChatType, ...]) -> int:
        return await ChatModel.find(
            ChatModel.last_saw >= datetime.now(timezone.utc) - timedelta(hours=48),
            ChatModel.first_saw >= datetime.now(timezone.utc) - timedelta(hours=48),
            In(ChatModel.type, chat_types),
        ).count()

    @staticmethod
    async def active_count_last_48h(chat_types: tuple[ChatType, ...]) -> int:
        return await ChatModel.find(
            ChatModel.last_saw >= datetime.now(timezone.utc) - timedelta(hours=48),
            ChatModel.first_saw <= datetime.now(timezone.utc) - timedelta(hours=48),
            In(ChatModel.type, chat_types),
        ).count()

    async def delete_chat(self):
        await self.delete(link_rule=DeleteRules.DELETE_LINKS)

    @staticmethod
    async def get_by_tid(chat_id: int) -> Optional["ChatModel"]:
        return await ChatModel.find_one(ChatModel.chat_id == chat_id)

    @staticmethod
    async def get_by_iid(iid: PydanticObjectId) -> Optional["ChatModel"]:
        return await ChatModel.find_one(ChatModel.id == iid)

    @staticmethod
    async def find_user(user_id: int) -> "ChatModel":
        user = await ChatModel.find_one(ChatModel.chat_id == user_id, ChatModel.type == ChatType.private)

        if not user:
            raise DBNotFoundException()

        return user

    @staticmethod
    async def find_user_by_username(username: str):
        user = await ChatModel.find_one(ChatModel.username == username)
        if not user:
            raise DBNotFoundException()

        return user

    @staticmethod
    def user_from_id(user_id: int) -> "ChatModel":
        return ChatModel(
            chat_id=user_id,
            first_name_or_title="User",
            is_bot=False,  # We don't know, but we can assume
            username=None,
            type=ChatType.private,
            last_saw=datetime.now(timezone.utc),
        )

    @staticmethod
    def export_dict(chat: "ChatModel") -> dict[str, Any]:
        return chat.model_dump(mode="json", exclude_none=True, exclude_unset=True, exclude_defaults=True)

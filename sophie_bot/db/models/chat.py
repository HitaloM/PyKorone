from datetime import datetime
from datetime import timezone
from enum import Enum
from typing import Optional, Annotated, Iterable, List, Any

from aiogram.types import User, Chat
from beanie import Document, Indexed, PydanticObjectId
from pydantic import Field
from pymongo import InsertOne


class ChatModel(Document):
    lang: str


class ChatType(Enum):
    group = "group"
    supergroup = "supergroup"
    private = "private"
    channel = "channel"


class ChatModel(Document):
    chat_id: Annotated[int, Indexed(unique=True)]
    type: ChatType = Field(..., description="Group type")
    first_name_or_title: str = Field(max_length=128)
    last_name: Optional[str] = Field(max_length=64, default=None)
    username: Annotated[Optional[str], Indexed()]
    is_bot: bool

    first_saw: datetime = Field(default_factory=datetime.utcnow)
    last_saw: datetime

    class Settings:
        name = "chats"

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
    async def upsert_user(user: User) -> ChatModel:
        data = ChatModel._get_user_data(user)
        existing_user: Optional[ChatModel] = await ChatModel.find_one(ChatModel.chat_id == user.id)
        if existing_user:
            return await existing_user.set(data)

        new_user = ChatModel(chat_id=user.id, **data)
        await new_user.save()
        return new_user

    @staticmethod
    async def upsert_group(chat: Chat) -> ChatModel:
        data = ChatModel._get_group_data(chat)
        existing_group: Optional[ChatModel] = await ChatModel.find_one(ChatModel.chat_id == chat.id)
        if existing_group:
            return await existing_group.set(data)

        new_group = ChatModel(chat_id=chat.id, **data)
        await new_group.save()
        return new_group

    @staticmethod
    async def do_bulk_upsert(chats: Iterable["ChatModel"]) -> List["ChatModel"]:
        return await ChatModel.bulk_write(
            [InsertOne(chat.dict(by_alias=True)) for chat in chats],
            ordered=False,
        )

    @staticmethod
    async def do_chat_migrate(old_id: int, new_chat: Chat) -> "ChatModel":
        chat = await ChatModel.find_one(ChatModel.chat_id == old_id)
        if chat:
            chat.chat_id = new_chat.id
            chat.type = ChatType[new_chat.type]
            await chat.save()
        return chat


class UserInGroupModel(Document):
    user_id: PydanticObjectId
    group_id: PydanticObjectId
    first_saw: datetime = Field(default_factory=datetime.utcnow)
    last_saw: datetime

    class Settings:
        name = "users_in_groups"

    @staticmethod
    async def ensure_user_in_group(user_id: PydanticObjectId, group_id: PydanticObjectId):
        data = {
            "user_id": user_id,
            "group_id": group_id,
            "last_saw": datetime.now(timezone.utc),
        }

        existing_link: Optional[UserInGroupModel] = await UserInGroupModel.find_one(
            UserInGroupModel.user_id == user_id, UserInGroupModel.group_id == group_id
        )
        if existing_link:
            return await existing_link.set(data)

        new_link = UserInGroupModel(**data)
        await new_link.save()
        return new_link

    @staticmethod
    async def remove_user_in_chat(user_id: PydanticObjectId, group_id: PydanticObjectId):
        user_in_chat = await UserInGroupModel.find_one(UserInGroupModel.user == user_id,
                                                       UserInGroupModel.group == group_id)
        if user_in_chat:
            await user_in_chat.delete()
        return user_in_chat


class ChatTopicModel(Document):
    group_id: PydanticObjectId
    thread_id: int
    name: Optional[str] = None
    last_active: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "chat_topics"

    @staticmethod
    async def ensure_topic(group_id: PydanticObjectId, thread_id: int, topic_name: Optional[str]):
        data = {
            "group_id": group_id,
            "thread_id": thread_id,
            "name": topic_name,
            "last_active": datetime.now(timezone.utc),
        }

        existing_link: Optional[ChatTopicModel] = await ChatTopicModel.find_one(
            ChatTopicModel.group_id == group_id, ChatTopicModel.thread_id == thread_id
        )
        if existing_link:
            return await existing_link.set(data)

        new_link = ChatTopicModel(**data)
        await new_link.save()
        return new_link

from datetime import datetime
from datetime import timezone
from enum import Enum
from typing import Optional, Annotated, Iterable, List, Any

from aiogram.types import User, Chat
from beanie import Document, Indexed, PydanticObjectId, Link, BackLink, DeleteRules
from beanie.odm.operators.update.general import Set
from pydantic import Field
from pymongo import InsertOne


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

    # User in groups
    user_in_groups: BackLink["UserInGroupModel"] = Field(original_field="user")
    groups_of_user: BackLink["UserInGroupModel"] = Field(original_field="group")

    # Topics
    chat_topics: BackLink["ChatTopicModel"] = Field(original_field="group")

    # Language
    language: BackLink["LanguageModel"] = Field(original_field="chat")

    # Connections
    user_connected: BackLink["ChatConnectionModel"] = Field(original_field="user")
    group_connected: BackLink["ChatConnectionModel"] = Field(original_field="group")

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
    async def upsert_user(user: User) -> "ChatModel":
        data = ChatModel._get_user_data(user)
        existing_user: Optional[ChatModel] = await ChatModel.find_one(ChatModel.chat_id == user.id)
        if existing_user:
            return await existing_user.set(data)

        new_user = ChatModel(chat_id=user.id, **data)
        await new_user.insert()
        return new_user

    @staticmethod
    async def upsert_group(chat: Chat) -> "ChatModel":
        data = ChatModel._get_group_data(chat)
        existing_group: Optional[ChatModel] = await ChatModel.find_one(ChatModel.chat_id == chat.id)
        if existing_group:
            return await existing_group.set(data)

        new_group = ChatModel(chat_id=chat.id, **data)
        await new_group.insert()
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

    async def delete_chat(self):
        await self.delete(link_rule=DeleteRules.DELETE_LINKS)


class UserInGroupModel(Document):
    user: Link[ChatModel]
    group: Link[ChatModel]
    first_saw: datetime = Field(default_factory=datetime.utcnow)
    last_saw: datetime

    class Settings:
        name = "users_in_groups"

    @staticmethod
    async def ensure_user_in_group(user: ChatModel, group: ChatModel):
        current_timedate = datetime.now(timezone.utc)

        return await UserInGroupModel.find_one(
            UserInGroupModel.user.id == user.id, UserInGroupModel.group.id == group.id,
        ).upsert(
            Set({UserInGroupModel.last_saw: current_timedate}),
            on_insert=UserInGroupModel(
                user=user,
                group=group,
                last_saw=current_timedate,
            )
        )

    @staticmethod
    async def remove_user_in_chat(user_iid: PydanticObjectId, group_iid: PydanticObjectId):
        user_in_chat = await UserInGroupModel.find_one(
            UserInGroupModel.user.id == user_iid, UserInGroupModel.group.id == group_iid
        )
        if user_in_chat:
            await user_in_chat.delete()
        return user_in_chat


class ChatTopicModel(Document):
    group: Link[ChatModel]
    thread_id: int
    name: Optional[str] = None
    last_active: datetime = Field(default_factory=datetime.utcnow)

    class Settings:
        name = "chat_topics"

    @staticmethod
    async def ensure_topic(group: ChatModel, thread_id: int, topic_name: Optional[str]):
        return await ChatTopicModel.find_one(
            ChatTopicModel.group.id == group.id, ChatTopicModel.thread_id == thread_id
        ).upsert(
            Set({ChatTopicModel.name: topic_name}) if topic_name else None,
            on_insert=ChatTopicModel(
                group=group,
                thread_id=thread_id,
                name=topic_name,
                last_active=datetime.now(timezone.utc),
            )
        )

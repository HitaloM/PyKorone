from typing import Optional

from beanie import Document, Link, PydanticObjectId, UpdateResponse
from beanie.odm.operators.update.general import Set

from sophie_bot.db.models import ChatModel


class WSUserModel(Document):
    user: Link["ChatModel"]
    group: Link["ChatModel"]
    passed: bool = False

    class Settings:
        name = "ws_users"

    @staticmethod
    async def ensure_user(user: "ChatModel", group: "ChatModel") -> "WSUserModel":
        return await WSUserModel.find_one(
            WSUserModel.user.id == user.id,
            WSUserModel.group.id == group.id,
        ).upsert(
            Set({}),
            on_insert=WSUserModel(
                user=user,
                group=group,
            ),
            response_type=UpdateResponse.NEW_DOCUMENT,
        )

    @staticmethod
    async def remove_user(user_iid: PydanticObjectId, group_iid: PydanticObjectId) -> Optional["WSUserModel"]:
        user_in_chat = await WSUserModel.find_one(WSUserModel.user.id == user_iid, WSUserModel.group.id == group_iid)
        if user_in_chat:
            await user_in_chat.delete()
        return user_in_chat

    @staticmethod
    async def is_user(user_iid: PydanticObjectId, group_iid: PydanticObjectId) -> Optional["WSUserModel"]:
        return await WSUserModel.find_one(WSUserModel.user.id == user_iid, WSUserModel.group.id == group_iid)

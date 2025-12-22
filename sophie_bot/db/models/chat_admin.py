from __future__ import annotations

from datetime import datetime, timezone

from aiogram.types import ResultChatMemberUnion
from beanie import Document, Link
from bson import ObjectId
from pydantic import Field

from sophie_bot.db.models import ChatModel


class ChatAdminModel(Document):
    chat: Link[ChatModel]
    user: Link[ChatModel]

    member: ResultChatMemberUnion
    last_updated: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    class Settings:
        name = "chat_admin"

    @staticmethod
    async def upsert_admin(chat_iid: ObjectId, user_iid, member: ResultChatMemberUnion):
        admin = await ChatAdminModel.find_one(
            ChatAdminModel.chat.id == chat_iid,  # type: ignore[attr-defined]
            ChatAdminModel.user.id == user_iid,  # type: ignore[attr-defined]
        )
        if not admin:
            admin = ChatAdminModel(chat=chat_iid, user=user_iid, member=member)
        else:
            admin.member = member
            admin.last_updated = datetime.now(timezone.utc)
        await admin.save()
        return admin

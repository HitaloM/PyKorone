from __future__ import annotations

from fastapi import HTTPException

from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.chat_admin import ChatAdminModel


async def verify_admin(chat: ChatModel, user: ChatModel) -> ChatModel:
    admin = await ChatAdminModel.find_one(
        ChatAdminModel.user.id == user.iid,  # type: ignore[attr-defined]
        ChatAdminModel.chat.id == chat.iid,  # type: ignore[attr-defined]
    )
    if not admin:
        raise HTTPException(status_code=403, detail="You are not an admin in this chat")

    return chat

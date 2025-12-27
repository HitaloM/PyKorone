from __future__ import annotations

from fastapi import HTTPException

from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.chat_admin import ChatAdminModel


async def get_chat_and_verify_admin(chat_id: int, user: ChatModel) -> ChatModel:
    chat = await ChatModel.get_by_tid(chat_id)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    admin = await ChatAdminModel.find_one(
        ChatAdminModel.user.id == user.id,  # type: ignore[attr-defined]
        ChatAdminModel.chat.id == chat.id,  # type: ignore[attr-defined]
    )
    if not admin:
        raise HTTPException(status_code=403, detail="You are not an admin in this chat")

    return chat

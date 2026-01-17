from datetime import datetime, timedelta, timezone
from typing import Optional

from sophie_bot.db.models.chat_connections import ChatConnectionModel
from sophie_bot.services.redis import redis


async def set_connected_chat(user_id: int, chat_id: Optional[int]):
    """
    Connects user to a chat.
    If chat_id is None, disconnects.
    Sets expiry to 48 hours from now.
    """
    # Clear legacy redis cache just in case
    redis.delete(f"connection_cache_{user_id}")

    if chat_id is None:
        if conn := await ChatConnectionModel.find_one(ChatConnectionModel.user_id == user_id):
            conn.chat_id = None
            conn.expires_at = None
            await conn.save()
        return

    expires_at = datetime.now(timezone.utc) + timedelta(hours=48)

    conn = await ChatConnectionModel.find_one(ChatConnectionModel.user_id == user_id)
    if conn:
        conn.chat_id = chat_id
        conn.expires_at = expires_at
        if chat_id not in conn.history:
            conn.history.append(chat_id)
        await conn.save()
    else:
        conn = ChatConnectionModel(user_id=user_id, chat_id=chat_id, expires_at=expires_at, history=[chat_id])
        await conn.insert()

from typing import Optional

from pydantic import BaseModel

from sophie_bot.services.redis import aredis


class MessageType(BaseModel):
    user_id: int
    message_id: int
    text: str


def get_key(chat_id: int) -> str:
    return f"messages:{chat_id}"


async def cache_message(text: Optional[str], chat_id: int, user_id: int, message_id: int):
    if not text:
        return

    msg = MessageType(
        user_id=user_id,
        message_id=message_id,
        text=text,
    )
    json_str = msg.model_dump_json()

    key = get_key(chat_id)

    await aredis.ltrim(key, -15, -1)  # type: ignore[misc]
    await aredis.expire(key, 86400 * 2, lt=True)  # type: ignore[misc] # 2 days
    await aredis.rpush(get_key(chat_id), json_str)  # type: ignore[misc]


async def reset_messages(chat_id: int):
    key = get_key(chat_id)
    await aredis.delete(key)  # type: ignore[misc]


async def get_cached_messages(chat_id: int) -> tuple[MessageType, ...]:
    return tuple(
        MessageType.model_validate_json(raw_msg)
        for raw_msg in await aredis.lrange(get_key(chat_id), 0, -1)  # type: ignore[misc]
    )

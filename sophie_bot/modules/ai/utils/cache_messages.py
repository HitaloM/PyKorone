from typing import Optional, Tuple

from pydantic import BaseModel

from sophie_bot.services.redis import aredis


class MessageType(BaseModel):
    user_id: int
    message_id: int
    text: str


def get_message_cache_key(chat_id: int) -> str:
    """Builds the Redis key for storing messages of a given chat."""
    return f"messages:{chat_id}"


async def cache_message(text: Optional[str], chat_id: int, user_id: int, message_id: int) -> None:
    """Caches a message if text is provided."""
    if not text:
        return

    msg = MessageType(
        user_id=user_id,
        message_id=message_id,
        text=text,
    )
    json_str = msg.model_dump_json()
    key = get_message_cache_key(chat_id)

    # Group commands in a pipeline to ensure atomic execution.
    async with aredis.pipeline(transaction=True) as pipe:
        await pipe.ltrim(key, -15, -1)  # type: ignore[misc]
        await pipe.expire(key, 86400 * 2, lt=True)
        await pipe.rpush(key, json_str)  # type: ignore[misc]
        await pipe.execute()


async def reset_messages(chat_id: int) -> None:
    """Resets the cached messages for a given chat."""
    key = get_message_cache_key(chat_id)
    await aredis.delete(key)


async def get_cached_messages(chat_id: int) -> Tuple[MessageType, ...]:
    """Retrieves and parses all the cached messages for a given chat."""
    key = get_message_cache_key(chat_id)
    raw_messages = await aredis.lrange(key, 0, -1)  # type: ignore[misc]
    messages = [MessageType.model_validate_json(raw_msg) for raw_msg in raw_messages]
    return tuple(sorted(messages, key=lambda x: x.message_id))

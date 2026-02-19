from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ValidationError

from korone import aredis
from korone.config import CONFIG
from korone.logger import get_logger

from .keys import ai_messages_key

logger = get_logger(__name__)


class MessageType(BaseModel):
    role: Literal["assistant", "user"]
    user_id: int
    name: str
    text: str


def _cache_limit() -> int:
    # Each interaction typically adds one user + one assistant message.
    return max(CONFIG.ai_max_context_messages * 2, 12)


async def cache_message(
    text: str | None, chat_id: int, user_id: int, role: Literal["assistant", "user"], name: str
) -> None:
    if not text:
        return

    message = MessageType(role=role, user_id=user_id, name=name, text=text)
    key = ai_messages_key(chat_id)
    payload = message.model_dump_json()

    async with aredis.pipeline(transaction=True) as pipe:
        await pipe.rpush(key, payload)  # type: ignore[misc]
        await pipe.ltrim(key, -_cache_limit(), -1)  # type: ignore[misc]
        await pipe.expire(key, 86400 * 7)  # type: ignore[misc]
        await pipe.execute()


async def reset_messages(chat_id: int) -> None:
    await aredis.delete(ai_messages_key(chat_id))


async def get_cached_messages(chat_id: int) -> tuple[MessageType, ...]:
    raw_messages = await aredis.lrange(ai_messages_key(chat_id), 0, -1)  # type: ignore[misc]
    parsed: list[MessageType] = []

    for item in raw_messages:
        try:
            parsed.append(MessageType.model_validate_json(item))
        except ValidationError:
            logger.warning("Invalid AI cache entry, skipping", chat_id=chat_id)

    return tuple(parsed)

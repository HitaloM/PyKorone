import json
from typing import TYPE_CHECKING

from aiogram.exceptions import TelegramBadRequest
from redis.exceptions import RedisError

from korone import aredis, bot
from korone.constants import CACHE_DEFAULT_TTL_SECONDS
from korone.db.repositories import chat as chat_repo
from korone.logging import get_logger

if TYPE_CHECKING:
    from aiogram.types import ResultChatMemberUnion

    from korone.db.models.chat import ChatModel

logger = get_logger(__name__)


async def get_chat_members(chat_id: int) -> list[ResultChatMemberUnion]:
    try:
        return await bot.get_chat_administrators(chat_id)
    except TelegramBadRequest as error:
        if "chat not found" in str(error).lower():
            await logger.adebug("chat_members: chat not found", chat_id=chat_id)
            return []
        raise


async def update_chat_members(chat: ChatModel) -> None:
    chat_members = await get_chat_members(chat.chat_id)
    admins_map: dict[str, dict] = {}

    for member in chat_members:
        user = await chat_repo.get_by_chat_id(member.user.id)
        if not user:
            await logger.adebug("user_details: user not found in database", user_id=member.user.id)
            continue

        admins_map[str(member.user.id)] = member.model_dump()

    key = f"chat_admins:{chat.chat_id}"
    try:
        await aredis.set(key, json.dumps(admins_map), ex=CACHE_DEFAULT_TTL_SECONDS)
        await logger.adebug("update_chat_members: updated redis cache", key=key, count=len(admins_map))
    except RedisError:
        await logger.adebug("update_chat_members: failed to set redis cache", key=key)

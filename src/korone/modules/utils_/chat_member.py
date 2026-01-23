import json

from aiogram.exceptions import TelegramBadRequest
from aiogram.types import ResultChatMemberUnion

from korone import aredis, bot
from korone.constants import CACHE_DEFAULT_TTL_SECONDS
from korone.db.models.chat import ChatModel
from korone.logging import get_logger

logger = get_logger(__name__)


async def get_chat_members(chat_tid: int) -> list[ResultChatMemberUnion]:
    try:
        return await bot.get_chat_administrators(chat_tid)
    except TelegramBadRequest as error:
        if "chat not found" in str(error).lower():
            await logger.adebug("chat_members: chat not found", chat_tid=chat_tid)
            return []
        raise


async def update_chat_members(chat: ChatModel) -> None:
    chat_members = await get_chat_members(chat.tid)
    admins_map: dict[str, dict] = {}

    for member in chat_members:
        user = await ChatModel.get_by_tid(member.user.id)
        if not user:
            await logger.adebug("user_details: user not found in database", user_id=member.user.id)
            continue

        admins_map[str(member.user.id)] = member.model_dump()

    key = f"chat_admins:{chat.tid}"
    try:
        await aredis.set(key, json.dumps(admins_map), ex=CACHE_DEFAULT_TTL_SECONDS)
        await logger.adebug("update_chat_members: updated redis cache", key=key, count=len(admins_map))
    except Exception:
        await logger.adebug("update_chat_members: failed to set redis cache", key=key)

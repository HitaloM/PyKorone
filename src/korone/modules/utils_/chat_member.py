from typing import TYPE_CHECKING, Any

from aiogram.exceptions import TelegramBadRequest

from korone import bot
from korone.db.repositories.chat import ChatRepository
from korone.db.repositories.chat_admin import ChatAdminRepository
from korone.logger import get_logger

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
    admins_map: dict[int, dict[str, Any]] = {}

    for member in chat_members:
        user = await ChatRepository.get_by_chat_id(member.user.id)
        if not user:
            user = await ChatRepository.upsert_user(member.user)

        admins_map[user.id] = member.model_dump(mode="json")

    await ChatAdminRepository.replace_chat_admins(chat, admins_map)
    await logger.adebug(
        "update_chat_members: updated admin cache in database", chat_id=chat.chat_id, count=len(admins_map)
    )

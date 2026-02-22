from typing import TYPE_CHECKING

from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.types import Chat

from korone.db.repositories.chat import ChatRepository
from korone.logger import get_logger

if TYPE_CHECKING:
    from aiogram import Bot

logger = get_logger(__name__)


def is_no_rights_error(exception: BaseException) -> bool:
    if not isinstance(exception, TelegramBadRequest):
        return False

    error_message = str(exception).lower()
    return "not enough rights" in error_message and "send" in error_message


async def handle_no_rights_error(bot: Bot, chat: Chat | None, exception: TelegramBadRequest) -> bool:
    if not isinstance(chat, Chat):
        logger.warning("Cannot handle no-rights error: no event_chat in data")
        return False

    chat_tid = chat.id
    logger.warning(
        "Bot lacks rights to send messages, leaving chat",
        chat_id=chat_tid,
        chat_title=getattr(chat, "title", "Unknown"),
        error=str(exception),
    )

    try:
        await bot.leave_chat(chat_tid)
        logger.info("Successfully left chat due to permission restrictions", chat_id=chat_tid)
    except TelegramAPIError as leave_error:
        logger.exception("Failed to leave chat", chat_id=chat_tid, error=str(leave_error))
        return False

    chat_model = await ChatRepository.get_by_chat_id(chat_tid)
    if chat_model:
        logger.info("Forced chat leave registered", chat_id=chat_tid, db_chat_id=chat_model.id)
    else:
        logger.warning("Chat model not found for forced leave", chat_id=chat_tid)

    return True

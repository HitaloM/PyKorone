from typing import TYPE_CHECKING, TypeGuard

from aiogram.exceptions import TelegramAPIError, TelegramBadRequest, TelegramForbiddenError
from aiogram.types import Chat

from korone.db.repositories.chat import ChatRepository
from korone.logger import get_logger

if TYPE_CHECKING:
    from aiogram import Bot

logger = get_logger(__name__)


RIGHTS_INDICATORS = (
    "not enough rights",
    "have no rights to send a message",
    "can't send messages",
    "cannot send messages",
    "chat write forbidden",
    "chat_write_forbidden",
    "bot is restricted",
    "user is restricted",
)


def _coerce_chat_id(raw_chat_id: int | str | None) -> int | None:
    if isinstance(raw_chat_id, int):
        return raw_chat_id

    if isinstance(raw_chat_id, str):
        try:
            return int(raw_chat_id)
        except ValueError:
            return None

    return None


def _extract_chat_id(chat: Chat | None, exception: TelegramBadRequest | TelegramForbiddenError) -> int | None:
    if isinstance(chat, Chat):
        return chat.id

    method_chat_id: int | str | None = getattr(exception.method, "chat_id", None)
    return _coerce_chat_id(method_chat_id)


def is_no_rights_error(exception: BaseException) -> TypeGuard[TelegramBadRequest | TelegramForbiddenError]:
    if not isinstance(exception, (TelegramBadRequest, TelegramForbiddenError)):
        return False

    error_message = str(exception).lower().replace("_", " ")
    return any(indicator in error_message for indicator in RIGHTS_INDICATORS)


async def handle_no_rights_error(
    bot: Bot, chat: Chat | None, exception: TelegramBadRequest | TelegramForbiddenError
) -> bool:
    chat_tid = _extract_chat_id(chat, exception)
    if chat_tid is None:
        await logger.awarning(
            "Cannot handle no-rights error: chat_id unavailable",
            error=str(exception),
            method=type(exception.method).__name__,
        )
        return False

    await logger.awarning(
        "Bot lacks rights to send messages, leaving chat",
        chat_id=chat_tid,
        chat_title=getattr(chat, "title", "Unknown"),
        method=type(exception.method).__name__,
        error=str(exception),
    )

    try:
        await bot.leave_chat(chat_tid)
        await logger.ainfo("Successfully left chat due to permission restrictions", chat_id=chat_tid)
    except TelegramAPIError as leave_error:
        await logger.aexception("Failed to leave chat", chat_id=chat_tid, error=str(leave_error))
        return False

    chat_model = await ChatRepository.get_by_chat_id(chat_tid)
    if chat_model:
        await ChatRepository.delete_chat(chat_model)
        await logger.ainfo(
            "Forced chat leave registered and chat removed from DB", chat_id=chat_tid, db_chat_id=chat_model.id
        )
    else:
        await logger.awarning("Chat model not found for forced leave", chat_id=chat_tid)

    return True

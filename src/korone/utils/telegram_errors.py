from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram.exceptions import TelegramBadRequest


def _normalized_message(error: TelegramBadRequest) -> str:
    return error.message.casefold().replace("_", " ")


def is_bot_not_admin_error(error: TelegramBadRequest) -> bool:
    return "bot not admin" in _normalized_message(error)


def is_callback_query_expired_error(error: TelegramBadRequest) -> bool:
    message = _normalized_message(error)
    return "query is too old" in message or "query id is invalid" in message


def is_message_not_modified_error(error: TelegramBadRequest) -> bool:
    return "message is not modified" in _normalized_message(error)


def is_message_to_edit_not_found_error(error: TelegramBadRequest) -> bool:
    return "message to edit not found" in _normalized_message(error)


def is_topic_closed_error(error: TelegramBadRequest) -> bool:
    return "topic closed" in _normalized_message(error)

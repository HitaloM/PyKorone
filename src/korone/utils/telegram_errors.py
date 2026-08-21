from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram.exceptions import TelegramBadRequest


def _normalized_message(error: TelegramBadRequest) -> str:
    return " ".join(error.message.casefold().replace("_", " ").split())


def _message_contains_any(error: TelegramBadRequest, indicators: tuple[str, ...]) -> bool:
    message = _normalized_message(error)
    return any(indicator in message for indicator in indicators)


def is_bot_not_admin_error(error: TelegramBadRequest) -> bool:
    return _message_contains_any(error, ("bot not admin", "chat admin required"))


def is_callback_query_expired_error(error: TelegramBadRequest) -> bool:
    return _message_contains_any(error, ("query is too old", "query id is invalid"))


def is_message_not_modified_error(error: TelegramBadRequest) -> bool:
    return "message is not modified" in _normalized_message(error)


def is_message_to_edit_not_found_error(error: TelegramBadRequest) -> bool:
    return "message to edit not found" in _normalized_message(error)


def is_message_to_reply_not_found_error(error: TelegramBadRequest) -> bool:
    return "message to be replied not found" in _normalized_message(error)


def is_topic_closed_error(error: TelegramBadRequest) -> bool:
    return "topic closed" in _normalized_message(error)

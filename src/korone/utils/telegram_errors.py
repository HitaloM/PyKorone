from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from aiogram.exceptions import TelegramAPIError, TelegramBadRequest


def normalized_error_message(error: TelegramAPIError) -> str:
    return " ".join(error.message.casefold().replace("_", " ").split())


def _message_contains_any(error: TelegramBadRequest, indicators: tuple[str, ...]) -> bool:
    message = normalized_error_message(error)
    return any(indicator in message for indicator in indicators)


def is_bot_not_admin_error(error: TelegramBadRequest) -> bool:
    return _message_contains_any(error, ("bot not admin", "chat admin required"))


def is_callback_query_expired_error(error: TelegramBadRequest) -> bool:
    return _message_contains_any(error, ("query is too old", "query id is invalid"))


def is_message_not_modified_error(error: TelegramBadRequest) -> bool:
    return "message is not modified" in normalized_error_message(error)


def is_message_to_edit_not_found_error(error: TelegramBadRequest) -> bool:
    return "message to edit not found" in normalized_error_message(error)


def is_message_to_reply_not_found_error(error: TelegramBadRequest) -> bool:
    return "message to be replied not found" in normalized_error_message(error)


def is_topic_closed_error(error: TelegramBadRequest) -> bool:
    return "topic closed" in normalized_error_message(error)


def is_chat_not_found_error(error: TelegramBadRequest) -> bool:
    return "chat not found" in normalized_error_message(error)


def is_message_delete_unavailable_error(error: TelegramBadRequest) -> bool:
    return _message_contains_any(error, ("message can't be deleted", "message to delete not found"))


def is_user_already_participant_error(error: TelegramBadRequest) -> bool:
    return "user already participant" in normalized_error_message(error)


def is_bad_media_url_error(error: TelegramBadRequest) -> bool:
    return _message_contains_any(error, ("wrong type of the web page content", "failed to get http url content"))

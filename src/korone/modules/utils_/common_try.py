from typing import TYPE_CHECKING

from aiogram.exceptions import (
    TelegramAPIError,
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramMigrateToChat,
    TelegramNotFound,
)

from korone.logger import get_logger
from korone.utils.telegram_errors import (
    is_message_delete_unavailable_error,
    is_message_to_reply_not_found_error,
    is_user_already_participant_error,
)
from korone.utils.telegram_permissions import is_no_rights_error

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

IGNORED_EXCEPTIONS = (TelegramNotFound, TelegramForbiddenError, TelegramMigrateToChat)

logger = get_logger(__name__)


async def common_try[T](to_try: Awaitable[T], reply_not_found: Callable[[], Awaitable[T]] | None = None) -> T | None:
    try:
        await logger.adebug("common_try: Trying to execute callback")
        return await to_try
    except TelegramBadRequest as err:
        if reply_not_found and is_message_to_reply_not_found_error(err):
            await logger.adebug("common_try: Reply not found, trying to execute reply_not_found")
            return await common_try(to_try=reply_not_found())
        if is_message_to_reply_not_found_error(err):
            await logger.adebug("common_try: Reply not found, ignoring")
            return None
        if is_message_delete_unavailable_error(err):
            await logger.adebug("common_try: Message can't be deleted, ignoring")
            return None
        if is_user_already_participant_error(err):
            await logger.adebug("common_try: User already participant, ignoring")
        else:
            await logger.awarning("common_try: Unknown TelegramBadRequest exception, re-raising", error=str(err))
            raise
    except IGNORED_EXCEPTIONS as err:
        if isinstance(err, TelegramForbiddenError) and is_no_rights_error(err):
            await logger.awarning("common_try: Re-raising no-rights error", error=str(err))
            raise
        await logger.adebug("common_try: Caught ignored exception", error=str(err))
        return None
    except TelegramAPIError as err:
        await logger.awarning("common_try: Other unhandled Telegram API error", error=str(err))
        raise

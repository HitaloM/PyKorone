from collections.abc import Awaitable, Callable

from aiogram.exceptions import (
    TelegramAPIError,
    TelegramBadRequest,
    TelegramForbiddenError,
    TelegramMigrateToChat,
    TelegramNotFound,
)

from korone.logger import get_logger
from korone.modules.error.utils.permission_errors import is_no_rights_error
from korone.modules.utils_.telegram_exceptions import (
    CAN_NOT_BE_DELETED,
    MSG_TO_DEL_NOT_FOUND,
    REPLIED_NOT_FOUND,
    USER_ALREADY_PARTICIPANT,
)

type COROUTINE_TYPE[T] = Awaitable[T]
type CALLBACK_COROUTINE_TYPE[T] = Callable[[], COROUTINE_TYPE[T]]
IGNORED_EXCEPTIONS = (TelegramNotFound, TelegramForbiddenError, TelegramMigrateToChat)

logger = get_logger(__name__)


async def common_try[T](
    to_try: COROUTINE_TYPE[T], reply_not_found: CALLBACK_COROUTINE_TYPE[T] | None = None
) -> T | None:
    try:
        await logger.adebug("common_try: Trying to execute callback")
        return await to_try
    except TelegramBadRequest as err:
        if reply_not_found and REPLIED_NOT_FOUND in err.message:
            await logger.adebug("common_try: Reply not found, trying to execute reply_not_found")
            return await common_try(to_try=reply_not_found())
        if REPLIED_NOT_FOUND in err.message:
            await logger.adebug("common_try: Reply not found, ignoring")
            return None
        if CAN_NOT_BE_DELETED in err.message:
            await logger.adebug("common_try: Message can't be deleted, ignoring")
            return None
        if MSG_TO_DEL_NOT_FOUND in err.message:
            await logger.adebug("common_try: Message to delete not found, ignoring")
            return None
        if USER_ALREADY_PARTICIPANT in err.message:
            await logger.adebug("common_try: User already participant, ignoring")
        else:
            await logger.aerror("common_try: Unknown TelegramBadRequest exception, re-raising", error=str(err))
            raise
    except IGNORED_EXCEPTIONS as err:
        if isinstance(err, TelegramForbiddenError) and is_no_rights_error(err):
            await logger.awarning("common_try: Re-raising no-rights error", error=str(err))
            raise
        await logger.adebug("common_try: Caught ignored exception", error=str(err))
        return None
    except TelegramAPIError as err:
        await logger.aerror("common_try: Other unhandled Telegram API error", error=str(err))
        raise

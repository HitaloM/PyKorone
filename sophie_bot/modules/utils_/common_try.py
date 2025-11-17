import logging
from typing import Any, Callable, Coroutine, Optional

from aiogram.exceptions import (
    TelegramAPIError,
    TelegramNotFound,
    TelegramForbiddenError,
    TelegramMigrateToChat,
    TelegramBadRequest,
)
from aiogram.methods import TelegramMethod

from sophie_bot.modules.utils_.telegram_exceptions import (
    CAN_NOT_BE_DELETED,
    MSG_TO_DEL_NOT_FOUND,
    REPLIED_NOT_FOUND,
)

COROUTINE_TYPE = Coroutine[Any, Any, Any] | TelegramMethod
CALLBACK_COROUTINE_TYPE = Callable[[], COROUTINE_TYPE]
IGNORED_EXCEPTIONS = (TelegramNotFound, TelegramForbiddenError, TelegramMigrateToChat)


async def common_try(to_try: COROUTINE_TYPE, reply_not_found: Optional[CALLBACK_COROUTINE_TYPE] = None) -> Any:
    """
    Catches common Telegram exceptions
    """
    try:
        logging.debug("common_try: Trying to execute callback")
        return await to_try
    except TelegramBadRequest as err:
        if reply_not_found and REPLIED_NOT_FOUND in err.message:
            logging.debug("common_try: Reply not found, trying to execute reply_not_found")
            return await common_try(to_try=reply_not_found())
        elif REPLIED_NOT_FOUND in err.message:
            logging.debug("common_try: Reply not found, ignoring")
            return None
        elif CAN_NOT_BE_DELETED in err.message:
            logging.debug("common_try: Message can't be deleted, ignoring")
            return None
        elif MSG_TO_DEL_NOT_FOUND in err.message:
            logging.debug("common_try: Message to delete not found, ignoring")
            return None
        else:
            logging.error(f"common_try: Unknown TelegramBadRequest exception ({err}), re-raising")
            raise err
    except IGNORED_EXCEPTIONS as err:
        logging.error(f"common_try: Caught: {err}, ignoring")
        return None
    except TelegramAPIError as err:
        logging.error(f"common_try: Other unhandled Telegram API error ({err})")
        raise err

import logging
from typing import Any, Callable, Coroutine, Optional

from aiogram.exceptions import TelegramAPIError, TelegramBadRequest
from aiogram.methods import TelegramMethod

from sophie_bot.modules.utils_.telegram_exceptions import (
    CAN_NOT_BE_DELETED,
    MSG_TO_DEL_NOT_FOUND,
    REPLIED_NOT_FOUND,
)

COROUTINE_TYPE = Coroutine[Any, Any, Any] | TelegramMethod
CALLBACK_COROUTINE_TYPE = Callable[[], COROUTINE_TYPE]


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
            logging.debug("common_try: Reply not found, skipping")
            return
        elif CAN_NOT_BE_DELETED in err.message:
            logging.debug("common_try: Message can't be deleted, skipping")
            return
        elif MSG_TO_DEL_NOT_FOUND in err.message:
            logging.debug("common_try: Message to delete not found, skipping")
        else:
            logging.exception("common_try: Unknown TelegramBadRequest exception")
            raise err
    except TelegramAPIError as err:
        logging.exception("common_try: Telegram API error")
        raise err

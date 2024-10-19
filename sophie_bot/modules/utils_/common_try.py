import logging
from typing import Any, Callable, Coroutine, Optional

from aiogram.exceptions import TelegramAPIError, TelegramBadRequest

from sophie_bot.modules.utils_.telegram_exceptions import REPLIED_NOT_FOUND

COROUTINE_TYPE = Coroutine[Any, Any, Any]
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
        else:
            logging.error("common_try: Unknown TelegramBadRequest exception", err)
            raise err
    except TelegramAPIError as err:
        logging.error("common_try: Telegram API error", err)
        raise err

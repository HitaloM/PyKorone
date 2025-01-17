from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramNetworkError,
    TelegramRetryAfter,
)
from pymongo.errors import DuplicateKeyError

IGNORED_EXCEPTIONS = (TelegramNetworkError, TelegramRetryAfter, TelegramBadRequest)
QUIET_EXCEPTIONS = (*IGNORED_EXCEPTIONS, DuplicateKeyError)

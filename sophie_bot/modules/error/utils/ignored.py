from aiogram.exceptions import (
    TelegramNetworkError,
    TelegramRetryAfter,
)
from pymongo.errors import DuplicateKeyError

IGNORED_EXCEPTIONS = (TelegramNetworkError, TelegramRetryAfter)
QUIET_EXCEPTIONS = (*IGNORED_EXCEPTIONS, DuplicateKeyError)

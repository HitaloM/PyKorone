from aiogram.exceptions import (
    TelegramNetworkError,
    TelegramRetryAfter,
    TelegramUnauthorizedError,
)
from pymongo.errors import DuplicateKeyError

IGNORED_EXCEPTIONS = (TelegramNetworkError, TelegramRetryAfter, TelegramUnauthorizedError)
QUIET_EXCEPTIONS = (*IGNORED_EXCEPTIONS, DuplicateKeyError)

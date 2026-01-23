from aiogram.exceptions import TelegramNetworkError, TelegramRetryAfter, TelegramUnauthorizedError
from sqlalchemy.exc import IntegrityError

IGNORED_EXCEPTIONS = (TelegramNetworkError, TelegramRetryAfter, TelegramUnauthorizedError)
QUIET_EXCEPTIONS = (*IGNORED_EXCEPTIONS, IntegrityError)

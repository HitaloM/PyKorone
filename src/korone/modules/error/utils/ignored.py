import asyncio

from aiogram.exceptions import (
    TelegramForbiddenError,
    TelegramNetworkError,
    TelegramRetryAfter,
    TelegramUnauthorizedError,
)
from sqlalchemy.exc import IntegrityError

from korone.utils.telegram_permissions import is_no_rights_error

IGNORED_EXCEPTIONS = (TelegramNetworkError, TelegramRetryAfter, TelegramUnauthorizedError)
QUIET_EXCEPTIONS = (*IGNORED_EXCEPTIONS, IntegrityError)


def is_expected_exception(exception: BaseException) -> bool:
    """Apply the same operational-error policy to every Sentry capture path."""
    if isinstance(exception, BaseExceptionGroup):
        return all(is_expected_exception(child) for child in exception.exceptions)
    return isinstance(exception, (*QUIET_EXCEPTIONS, asyncio.CancelledError, TimeoutError, TelegramForbiddenError)) or (
        is_no_rights_error(exception)
    )

from aiogram.exceptions import TelegramNetworkError, TelegramRetryAfter
from pymongo.errors import DuplicateKeyError
from telethon.errors import ChatWriteForbiddenError

IGNORED_EXCEPTIONS = (TelegramNetworkError, ChatWriteForbiddenError, TelegramRetryAfter)
QUIET_EXCEPTIONS = (*IGNORED_EXCEPTIONS, DuplicateKeyError)

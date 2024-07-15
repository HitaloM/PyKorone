from aiogram.exceptions import TelegramNetworkError, TelegramRetryAfter
from telethon.errors import ChatWriteForbiddenError

IGNORED_EXCEPTIONS = (TelegramNetworkError, ChatWriteForbiddenError, TelegramRetryAfter)

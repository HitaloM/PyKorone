from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from sophie_bot.utils.logger import log


class OrMiddleware(BaseMiddleware):
    def __init__(self, *middlewares):
        self.middlewares = middlewares

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        for middleware in self.middlewares:
            try:
                return await middleware(handler, event, data)
            except Exception as e:
                log.error("OrMiddleware: trying next one!", e=e, middleware=middleware)

from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from sophie_bot.utils.logger import log


class OrMiddleware(BaseMiddleware):
    def __init__(self, *middlewares: BaseMiddleware):
        self.middlewares = middlewares

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        last_exception: BaseException | None = None

        for middleware in self.middlewares:
            try:
                return await middleware(handler, event, data)
            except Exception as exc:
                log.warning("OrMiddleware: middleware failed, trying next", exc=exc, middleware=middleware)
                last_exception = exc

        # All middlewares failed - re-raise the last exception
        if last_exception is not None:
            raise last_exception

        # No middlewares configured
        return await handler(event, data)

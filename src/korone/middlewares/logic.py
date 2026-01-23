from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from korone.logging import get_logger

logger = get_logger(__name__)


class OrMiddleware(BaseMiddleware):
    __slots__ = ("middlewares",)

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
                await logger.awarning("OrMiddleware: middleware failed, trying next", exc=exc, middleware=middleware)
                last_exception = exc

        if last_exception is not None:
            raise last_exception

        return await handler(event, data)

from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware

from korone.logger import get_logger

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aiogram.types import TelegramObject

logger = get_logger(__name__)


class OrMiddleware(BaseMiddleware):
    __slots__ = ("middlewares",)

    def __init__(self, *middlewares: BaseMiddleware) -> None:
        self.middlewares = middlewares

    async def __call__(
        self, handler: Callable[[TelegramObject, Any], Awaitable[Any]], event: TelegramObject, data: Any
    ) -> Any:
        last_exception: BaseException | None = None

        for middleware in self.middlewares:
            try:
                return await middleware(handler, event, data)
            except Exception as exc:  # noqa: BLE001
                await logger.awarning("OrMiddleware: middleware failed, trying next", exc=exc, middleware=middleware)
                last_exception = exc

        if last_exception is not None:
            raise last_exception

        return await handler(event, data)

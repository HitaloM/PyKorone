from typing import TYPE_CHECKING

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from korone.logger import get_logger

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

logger = get_logger(__name__)

type HandlerResult = TelegramObject | bool | None
type MiddlewareDataValue = str | int | float | bool | TelegramObject | dict[str, str | int | float | bool | None] | None
type MiddlewareData = dict[str, MiddlewareDataValue]


class OrMiddleware(BaseMiddleware):
    __slots__ = ("middlewares",)

    def __init__(self, *middlewares: BaseMiddleware) -> None:
        self.middlewares = middlewares

    async def __call__(
        self,
        handler: Callable[[TelegramObject, MiddlewareData], Awaitable[HandlerResult]],
        event: TelegramObject,
        data: MiddlewareData,
    ) -> HandlerResult:
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

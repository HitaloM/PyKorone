from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import Update
from devtools import Debug

debug = Debug(highlight=True)


class UpdateDebugMiddleware(BaseMiddleware):
    async def __call__(
        self, handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]], update: Update, data: Dict[str, Any]
    ) -> Any:
        debug(update)
        return await handler(update, data)


class DataDebugMiddleware(BaseMiddleware):
    async def __call__(
        self, handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]], update: Update, data: Dict[str, Any]
    ) -> Any:
        debug(data)
        return await handler(update, data)


class HandlerDebugMiddleware(BaseMiddleware):
    async def __call__(
        self, handler: Callable[[Update, Dict[str, Any]], Awaitable[Any]], update: Update, data: Dict[str, Any]
    ) -> Any:
        debug(handler)
        result = await handler(update, data)
        debug(result)
        return result

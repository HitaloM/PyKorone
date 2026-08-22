from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aiogram.types import TelegramObject

    from korone.modules.inline.registry import InlineQueryRegistry

INLINE_QUERY_REGISTRY_KEY = "inline_query_registry"


class InlineQueryRegistryMiddleware(BaseMiddleware):
    def __init__(self) -> None:
        self._registry: InlineQueryRegistry | None = None

    def configure(self, registry: InlineQueryRegistry) -> None:
        self._registry = registry

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[object]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> object:
        if self._registry is None:
            msg = "Inline query registry middleware is not configured"
            raise RuntimeError(msg)
        data[INLINE_QUERY_REGISTRY_KEY] = self._registry
        return await handler(event, data)

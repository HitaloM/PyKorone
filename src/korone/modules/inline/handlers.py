from typing import TYPE_CHECKING, override

from korone.utils.handlers import KoroneInlineQueryHandler

from .middlewares import INLINE_QUERY_REGISTRY_KEY
from .registry import InlineQueryRegistry

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType

INLINE_QUERY_CACHE_SECONDS = 5


class InlineQueryAggregatorHandler(KoroneInlineQueryHandler):
    @classmethod
    @override
    def filters(cls) -> tuple[CallbackType, ...]:
        return ()

    @override
    async def handle(self) -> None:
        registry = self.data.get(INLINE_QUERY_REGISTRY_KEY)
        if not isinstance(registry, InlineQueryRegistry):
            msg = "Inline query registry is unavailable"
            raise TypeError(msg)

        results, button = await registry.collect(self.event)
        await self.event.answer(
            results, cache_time=INLINE_QUERY_CACHE_SECONDS, is_personal=True, next_offset="", button=button
        )

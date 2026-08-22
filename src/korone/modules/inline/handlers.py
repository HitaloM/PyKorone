from typing import TYPE_CHECKING, override

from korone.utils.handlers import KoroneInlineQueryHandler

from .registry import collect_inline_query_results

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
        results, button = await collect_inline_query_results(self.event)
        await self.event.answer(
            results, cache_time=INLINE_QUERY_CACHE_SECONDS, is_personal=True, next_offset="", button=button
        )

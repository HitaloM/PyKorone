import tracemalloc
from random import randint
from typing import Any, Awaitable, Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from sophie_bot.utils.logger import log

FIRST_SNAPSHOT = None


class TracemallocMiddleware(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: dict[str, Any],
    ) -> Any:
        result = await handler(event, data)

        global FIRST_SNAPSHOT
        if not FIRST_SNAPSHOT:
            FIRST_SNAPSHOT = tracemalloc.take_snapshot()
            log.info("Tracemalloc: first snapshot taken...")
            return result

        # 1% that it'll handle
        if randint(0, 100) != 0:
            return result

        snapshot = tracemalloc.take_snapshot()

        top_stats = snapshot.compare_to(FIRST_SNAPSHOT, 'lineno')

        log.info("Tracemalloc: " + "\n".join(map(str, top_stats[:10])))

        return result

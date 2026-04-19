from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any, Final

from aiogram import BaseMiddleware
from aiogram.types import Message

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aiogram.types import TelegramObject

EXCLAMATION_COMMAND_PATTERN: Final[re.Pattern[str]] = re.compile(r"^![A-Za-z0-9_]+(?:@[A-Za-z0-9_]+)?(?:\s|$)")


class CommandPrefixMiddleware(BaseMiddleware):
    """Normalizes commands with ! prefix to / prefix before routing."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message) and event.text and EXCLAMATION_COMMAND_PATTERN.match(event.text):
            event = event.model_copy(update={"text": f"/{event.text[1:]}"})

        return await handler(event, data)

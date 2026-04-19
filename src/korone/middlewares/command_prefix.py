from __future__ import annotations

import re
from typing import TYPE_CHECKING, Any

from aiogram import BaseMiddleware
from aiogram.types import Message

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from aiogram.types import TelegramObject

COMMAND_WITH_EXCLAMATION_PATTERN = re.compile(r"^![A-Za-z0-9_]+(?:@[A-Za-z0-9_]+)?(?:\s|$)")


class CommandPrefixMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            text = event.text
            if text and COMMAND_WITH_EXCLAMATION_PATTERN.match(text):
                event.__dict__["text"] = f"/{text[1:]}"

        return await handler(event, data)

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from collections.abc import Callable
from typing import TYPE_CHECKING

from hydrogram.filters import Filter

from korone.handlers.callback_query_handler import KoroneCallbackQueryHandler
from korone.handlers.error_handler import KoroneErrorHandler
from korone.handlers.message_handler import KoroneMessageHandler

if TYPE_CHECKING:
    from hydrogram.handlers.handler import Handler


class Factory:
    __slots__ = ("event_name", "events_observed")

    def __init__(self, event_name: str) -> None:
        self.event_name = event_name

        self.events_observed: dict[str, type[Handler]] = {
            "message": KoroneMessageHandler,
            "callback_query": KoroneCallbackQueryHandler,
            "error": KoroneErrorHandler,
        }

    def __call__(self, filters: Filter | None = None, group: int = 0) -> Callable:
        def wrapper(func: Callable) -> Callable:
            if not hasattr(func, "handlers"):
                func.handlers = []

            handler_class = self.events_observed.get(self.event_name)
            if handler_class is None:
                msg = f"No handler found for event: {self.event_name}"
                raise ValueError(msg)

            func.handlers.append((handler_class(func, filters), group))  # type: ignore

            return func

        return wrapper

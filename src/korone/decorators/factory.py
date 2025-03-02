# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, ClassVar

from korone.handlers.callback_query_handler import KoroneCallbackQueryHandler
from korone.handlers.error_handler import KoroneErrorHandler
from korone.handlers.message_handler import KoroneMessageHandler

if TYPE_CHECKING:
    from collections.abc import Callable

    from hydrogram.filters import Filter
    from hydrogram.handlers.handler import Handler


class Factory:
    __slots__ = ("update_name",)

    updates_observed: ClassVar[dict[str, type[Handler]]] = {
        "message": KoroneMessageHandler,
        "callback_query": KoroneCallbackQueryHandler,
        "error": KoroneErrorHandler,
    }

    def __init__(self, update_name: str) -> None:
        self.update_name = update_name

    def __call__(self, filters: Filter | None = None, group: int = 0) -> Callable:
        def wrapper(func: Callable) -> Callable:
            if not hasattr(func, "handlers"):
                func.handlers = []

            handler_class = self.updates_observed.get(self.update_name)
            if handler_class is None:
                msg = f"No handler found for update: {self.update_name}"
                raise ValueError(msg)

            func.handlers.append((handler_class(func, filters), group))  # type: ignore

            return func

        return wrapper

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from hydrogram.filters import Filter

from korone.handlers.callback_query_handler import KoroneCallbackQueryHandler
from korone.handlers.message_handler import KoroneMessageHandler

if TYPE_CHECKING:
    from hydrogram.handlers.handler import Handler


@dataclass(frozen=True, slots=True)
class HandlerObject:
    func: Callable
    filters: Filter
    group: int
    event: Callable


class Factory:
    __slots__ = ("event_name", "events_observed")

    def __init__(self, event_name: str) -> None:
        self.event_name = event_name

        self.events_observed: dict[str, type[Handler]] = {
            "message": KoroneMessageHandler,
            "callback_query": KoroneCallbackQueryHandler,
        }

    def __call__(self, filters: Filter, group: int = 0) -> Callable:
        def wrapper(func: Callable) -> Callable:
            func.on = self.event_name
            func.group = group
            func.filters = filters
            func.handlers = HandlerObject(
                func, filters, group, self.events_observed[self.event_name]
            )

            return func

        return wrapper

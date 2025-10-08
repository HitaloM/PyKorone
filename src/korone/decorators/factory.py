# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, Any, ClassVar, TypeVar

from korone.handlers.callback_query_handler import KoroneCallbackQueryHandler
from korone.handlers.error_handler import KoroneErrorHandler
from korone.handlers.message_handler import KoroneMessageHandler

if TYPE_CHECKING:
    from hydrogram.filters import Filter
    from hydrogram.handlers.handler import Handler

T = TypeVar("T", bound=Callable[..., Any])


class Factory:
    """Factory class for creating event handlers.

    This class is responsible for creating handlers for different types of events.
    It provides a decorator that can be used to register a function as a handler
    for a specific event type.
    """

    __slots__ = ("update_name",)

    updates_observed: ClassVar[dict[str, type[Handler]]] = {
        "message": KoroneMessageHandler,
        "callback_query": KoroneCallbackQueryHandler,
        "error": KoroneErrorHandler,
    }

    def __init__(self, update_name: str) -> None:
        """Initialize a new Factory instance.

        Args:
            update_name: The name of the update type to handle.
        """
        self.update_name = update_name

    def __call__(self, filters: Filter | None = None, group: int = 0) -> Callable[[T], T]:
        """Create a decorator for the specified update type.

        Args:
            filters: Optional filters to apply to the handler.
            group: The group to add the handler to.

        Returns:
            A decorator function that registers the decorated function as a handler.

        Raises:
            ValueError: If no handler is found for the update type.
        """

        handler_class = self.updates_observed.get(self.update_name)
        if handler_class is None:
            msg = f"No handler found for update: {self.update_name}"
            raise ValueError(msg)

        def wrapper(func: T) -> T:
            if not hasattr(func, "handlers"):
                func.handlers = []

            func.handlers.append((handler_class(func, filters), group))  # type: ignore

            return func

        return wrapper

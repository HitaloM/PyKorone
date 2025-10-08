# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from __future__ import annotations

from typing import Any

from .factory import Factory


class RouterError(Exception):
    """Exception raised for router-related errors."""

    pass


class Router:
    """Router class for handling different types of events.

    This class provides a centralized way to register handlers for different
    types of events. It uses a Factory instance for each event type to create
    the appropriate handler.
    """

    __slots__ = ("_factories",)

    def __init__(self) -> None:
        """Initialize a new Router instance with default event factories."""
        self._factories: dict[str, Factory] = {
            "message": Factory("message"),
            "callback_query": Factory("callback_query"),
            "error": Factory("error"),
        }

    def __getattr__(self, name: str) -> Factory:
        """Get a factory for the specified event type.

        Args:
            name: The name of the event type.

        Returns:
            The factory instance for the event type.

        Raises:
            RouterError: If the event type is not supported.
        """
        if name not in self._factories:
            msg = f"Event of type '{name}' is not supported by Korone."
            raise RouterError(msg)
        return self._factories[name]

    def message(self, *args: Any, **kwargs: Any) -> Any:
        """Decorator for message handlers.

        This is a convenience method that delegates to the message factory.

        Returns:
            Any: The decorator produced by the message factory.
        """
        return self._factories["message"](*args, **kwargs)

    def callback_query(self, *args: Any, **kwargs: Any) -> Any:
        """Decorator for callback query handlers.

        This is a convenience method that delegates to the callback_query factory.

        Returns:
            Any: The decorator produced by the callback_query factory.
        """
        return self._factories["callback_query"](*args, **kwargs)

    def error(self, *args: Any, **kwargs: Any) -> Any:
        """Decorator for error handlers.

        This is a convenience method that delegates to the error factory.

        Returns:
            Any: The decorator produced by the error factory.
        """
        return self._factories["error"](*args, **kwargs)

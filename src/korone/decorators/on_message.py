# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from collections.abc import Callable

from hydrogram.filters import Filter

from .i18n import use_gettext


class OnMessage:
    @staticmethod
    def on_message(filters: Filter, group: int = 0) -> Callable:
        """
        Decorator for registering a function as a message handler.

        This decorator registers a function as a message handler. The function
        must take a Client object and a Message object as parameters. The function
        must also be a coroutine function.

        Parameters
        ----------
        filters : hydrogram.filters.Filter
            The filters to apply to the incoming message.
        group : int, optional
            The group ID of the function, used for grouping related functions together.

        Returns
        -------
        collections.abc.Callable
            The decorated function.
        """

        def decorator(func: Callable) -> Callable:
            func.on = "message"
            func.group = group
            func.filters = filters

            return use_gettext(func)

        return decorator

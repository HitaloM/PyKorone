# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from collections.abc import Callable

from hydrogram.filters import Filter

from .i18n import use_gettext


class OnCallbackQuery:
    @staticmethod
    def on_callback_query(filters: Filter, group: int = 0) -> Callable:
        """
        Decorator for registering a function as a callback query handler.

        This decorator registers a function as a callback query handler. The function
        must take a Client object and a CallbackQuery object as parameters. The function
        must also be a coroutine function.

        Parameters
        ----------
        filters : hydrogram.filters.Filter
            The filters to apply to the incoming callback query.
        group : int, optional
            The group ID of the function, used for grouping related functions together.

        Returns
        -------
        collections.abc.Callable
            The decorated function.
        """

        def decorator(func: Callable) -> Callable:
            func.on = "callback_query"
            func.group = group
            func.filters = filters

            return use_gettext(func)

        return decorator

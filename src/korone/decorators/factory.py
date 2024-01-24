# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from collections.abc import Callable

from hydrogram.filters import Filter

from korone.decorators.i18n import use_gettext


class Factory:
    """
    Factory class to create decorators.

    This class is used to create a decorator, it receives the name of the event
    as a parameter and returns the class that will be used to create the
    decorator.

    Parameters
    ----------
    event_name : str
        The name of the event.

    Attributes
    ----------
    event_name : str
        The name of the event.
    """

    def __init__(self, event_name: str) -> None:
        self.event_name = event_name

    def __call__(self, filters: Filter, group: int = 0) -> Callable:
        """
        Execute the decorator when the decorated function is called.

        This method is used to create a decorator, it receives the filters and
        the group number as parameters and returns the decorator.

        Parameters
        ----------
        filters : hydrogram.filters.Filter
            The filter object used to determine if the decorated function should be executed.
        group : int, optional
            The group number for the decorated function, used for ordering the execution of
            multiple decorated functions.

        Returns
        -------
        collections.abc.Callable
            The decorated function.
        """

        def wrapper(func: Callable) -> Callable:
            func.on = self.event_name
            func.group = group
            func.filters = filters

            return use_gettext(func)

        return wrapper

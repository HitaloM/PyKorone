# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

from hydrogram.filters import Filter
from hydrogram.handlers import CallbackQueryHandler
from magic_filter import MagicFilter

from korone.decorators.save_chats import ChatManager
from korone.handlers import MagicMessageHandler

if TYPE_CHECKING:
    from hydrogram.handlers.handler import Handler


@dataclass(frozen=True, slots=True)
class HandlerObject:
    """
    A dataclass to store information about the handler.

    This dataclass is used to store information about the handler, it stores
    the function, the filters, the group number and the event name.
    """

    func: Callable
    """The function to be executed when the event is triggered.

    :type: collections.abc.Callable
    """
    filters: Filter | MagicFilter
    """The filter object used to determine if the function should be executed.

    :type: hydrogram.filters.Filter
    """
    group: int
    """The group number for the function, used for ordering the execution of
    multiple functions.

    :type: int
    """
    event: Callable
    """The event handler.

    :type: collections.abc.Callable
    """


class Factory:
    """
    Factory class to create decorators.

    This class is used to create a decorator. It receives the name of the event
    as a parameter and returns the class that will be used to create the decorator.

    Parameters
    ----------
    event_name : str
        The name of the event.

    Attributes
    ----------
    event_name : str
        The name of the event.
    events_observed : dict
        A dictionary that stores the events observed by the factory.
    """

    __slots__ = ("chat_manager", "event_name", "events_observed")

    def __init__(self, event_name: str) -> None:
        self.event_name = event_name
        self.chat_manager = ChatManager()

        self.events_observed: dict[str, type[Handler]] = {
            "message": MagicMessageHandler,
            "callback_query": CallbackQueryHandler,
        }

    def __call__(self, filters: Filter | MagicFilter, group: int = 0) -> Callable:
        """
        Execute the decorator when the decorated function is called.

        This method is used to create a decorator. It receives the filters and
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
            func.handlers = HandlerObject(
                func, filters, group, self.events_observed[self.event_name]
            )

            return self.chat_manager.handle_chat(func)

        return wrapper

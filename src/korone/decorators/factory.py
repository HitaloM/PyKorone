# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from typing import TYPE_CHECKING

from hairydogm.filters.callback_data import CallbackQueryFilter
from hydrogram.enums import ChatType
from hydrogram.handlers import CallbackQueryHandler
from hydrogram.types import CallbackQuery
from magic_filter import MagicFilter

from korone import i18n
from korone.decorators.language import LanguageManager
from korone.decorators.save_chats import ChatManager
from korone.filters.base import KoroneFilter
from korone.handlers import MagicMessageHandler

if TYPE_CHECKING:
    from hydrogram.handlers.handler import Handler

KoroneFilters = KoroneFilter | MagicFilter | CallbackQueryFilter


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
    filters: KoroneFilters
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

    __slots__ = ("chat_manager", "event_name", "events_observed", "language_manager")

    def __init__(self, event_name: str) -> None:
        self.event_name = event_name
        self.chat_manager = ChatManager()
        self.language_manager = LanguageManager()

        self.events_observed: dict[str, type[Handler]] = {
            "message": MagicMessageHandler,
            "callback_query": CallbackQueryHandler,
        }

    def __call__(self, filters: KoroneFilters, group: int = 0) -> Callable:
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

            @wraps(func)
            async def wrapped(*args, **kwargs):
                update = args[2] if len(args) > 2 else args[1]  # type: ignore
                is_callback = isinstance(update, CallbackQuery)
                message = update.message if is_callback else update
                user = update.from_user if is_callback else message.from_user

                if user and not user.is_bot:
                    if is_callback:
                        await self.chat_manager.save_from_user(user)
                    else:
                        await self.chat_manager.handle_message(message)

                chat = message.chat
                locale = i18n.default_locale
                if chat.type == ChatType.PRIVATE:
                    locale = await self.language_manager.get_locale(user)
                elif chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
                    locale = await self.language_manager.get_locale(chat)

                with i18n.context(), i18n.use_locale(locale):
                    return await func(*args, **kwargs)

            return wrapped

        return wrapper

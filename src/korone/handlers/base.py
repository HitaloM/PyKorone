# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import inspect
from collections.abc import Callable

from hydrogram import Client
from hydrogram.enums import ChatType
from hydrogram.filters import Filter
from hydrogram.types import CallbackQuery, Message, Update, User

from korone import i18n
from korone.handlers.database.language import get_locale
from korone.handlers.database.save_chats import handle_message, save_from_user


class BaseHandler:
    """
    A base handler class for processing updates from a messaging client.

    This class provides a framework for handling updates from a messaging client, such as messages
    or callback queries. It is designed to be subclassed to create specific handlers for different
    types of updates.

    Parameters
    ----------
    callback : Callable
        The callback function that will be called if the update passes the filters.
    filters : Filter | None, optional
        A filter object used to determine if an update should be processed by this handler.
    """

    __slots__ = ("callback", "filters")

    def __init__(self, callback: Callable, filters: Filter | None = None) -> None:
        self.callback = callback
        self.filters = filters

    @staticmethod
    async def _get_message_and_user_from_update(
        update: Update,
    ) -> tuple[Message, User]:
        """
        Extracts and returns the message and user from the given update.

        This method is used to extract the message and user from an update, such as a message or
        callback query. It is designed to be used internally by the handler to simplify the
        processing of updates.

        Parameters
        ----------
        update : Update
            The update to extract the message and user from.

        Returns
        -------
        tuple[Message, User]
            A tuple containing the message and the user who sent the message.

        Raises
        ------
        ValueError
            If the update type is not recognized.
        """
        if isinstance(update, CallbackQuery):
            return update.message, update.from_user
        if isinstance(update, Message):
            return update, update.from_user
        msg = f"Invalid update type: {type(update)}"
        raise ValueError(msg)

    async def _get_locale(self, update: Update) -> str:
        """
        Determines the locale to use based on the update's user or chat.

        This method is used to determine the locale to use for the update based on the user or chat
        that sent the message. It is designed to be used internally by the handler to simplify the
        processing of updates.

        Parameters
        ----------
        update : Update
            The update to determine the locale for.

        Returns
        -------
        str
            The determined locale as a string.
        """
        message, user = await self._get_message_and_user_from_update(update)
        chat = message.chat

        if user and chat.type == ChatType.PRIVATE:
            return await get_locale(user)
        if chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
            return await get_locale(chat)
        return i18n.default_locale

    async def _handle_update(self, client: Client, update: Update) -> Callable | None:
        """
        Processes an update.

        Processes the update, saves relevant data, and calls the handler's callback if conditions
        are met.

        Parameters
        ----------
        client : Client
            The client instance.
        update : Update
            The update to be processed.

        Returns
        -------
        Callable | None
            The callback function to be called, or None if the update should not be processed
            further.
        """

        try:
            message, user = await self._get_message_and_user_from_update(update)
        except ValueError:
            return None

        if isinstance(update, CallbackQuery):
            await save_from_user(user)
        else:  # Message
            await handle_message(message)

        if user and not user.is_bot and message:
            return await self.callback(client, update)

        return None

    async def _check(self, client: Client, update: Update) -> bool:
        """
        Checks if the update passes the handler's filters.

        Checks if the update passes the handler's filters. If the filters are not set, the update
        is considered to pass.

        Parameters
        ----------
        client : Client
            The client instance.
        update : Update
            The update to check.

        Returns
        -------
        bool
            True if the update passes the filters, False otherwise.
        """
        try:
            message, _ = await self._get_message_and_user_from_update(update)
        except ValueError:
            return False

        if not message or not callable(self.filters):
            return False

        if inspect.iscoroutinefunction(self.filters.__call__):
            return await self.filters(client, update)
        return await client.loop.run_in_executor(client.executor, self.filters, client, update)  # type: ignore

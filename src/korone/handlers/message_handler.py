# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from collections.abc import Callable
from inspect import iscoroutinefunction
from typing import Any

from hydrogram import Client
from hydrogram.handlers import MessageHandler
from hydrogram.types import Message
from magic_filter import MagicFilter

from korone.filters.base import KoroneFilter


class MagicMessageHandler(MessageHandler):
    """
    A message handler that can use magic filters.

    This class is a subclass of the MessageHandler class. It allows the use of
    magic filters in the handler. Magic filters are filters that can be used
    to determine if the handler should be executed.

    Parameters
    ----------
    callback : collections.abc.Callable
        The function to be executed when the event is triggered.
    filters : hydrogram.filters.Filter | magic_filter.MagicFilter | None
        The filter object used to determine if the function should be executed.

    References
    ----------
    - `MagicFilter <https://docs.aiogram.dev/en/dev-3.x/dispatcher/filters/magic_filters.html>`_
    """

    def __init__(
        self, callback: Callable[..., Any], filters: KoroneFilter | MagicFilter | None = None
    ):
        self.callback: Callable[..., Any] = callback
        self.filters: KoroneFilter | MagicFilter | None = filters

    async def check(self, client: Client, message: Message) -> bool:
        """
        Check if the handler should be executed.

        This method is used to check if the handler should be executed. It
        checks if the message has a matching listener and if the filters
        return True.

        Parameters
        ----------
        client : Client
            The client that received the message.
        message : Message
            The message that was received.

        Returns
        -------
        bool
            True if the handler should be executed, False otherwise.
        """
        listener_does_match, _ = await self.check_if_has_matching_listener(client, message)

        if listener_does_match:
            return True

        if not callable(self.filters):
            return False

        if isinstance(self.filters, MagicFilter):
            handler_does_match = await client.loop.run_in_executor(
                client.executor, self.filters.resolve, message
            )
        elif iscoroutinefunction(self.filters.__call__):
            handler_does_match = await self.filters(client, message)
        else:
            handler_does_match = await client.loop.run_in_executor(
                client.executor, self.filters, client, message
            )

        return bool(handler_does_match)

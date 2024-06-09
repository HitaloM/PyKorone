# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from collections.abc import Callable

from hydrogram import Client
from hydrogram.filters import Filter
from hydrogram.handlers import MessageHandler
from hydrogram.types import Message

from korone import i18n
from korone.handlers.base import BaseHandler


class KoroneMessageHandler(MessageHandler, BaseHandler):
    """
    A handler for processing messages in the Korone.

    This class inherits from both MessageHandler and BaseHandler to provide a specialized handler
    for processing messages. It integrates locale handling based on the message's origin, allowing
    for localized responses.

    Parameters
    ----------
    callback : Callable
        The callback function that will be called if the message passes the filters.
    filters : Filter | None, optional
        A filter object used to determine if a message should be processed by this handler.
    """

    __slots__ = ()

    def __init__(self, callback: Callable, filters: Filter | None = None) -> None:
        MessageHandler.__init__(self, callback, filters)  # type: ignore
        BaseHandler.__init__(self, callback, filters)

    async def check(self, client: Client, message: Message) -> None | Callable:
        """
        Checks if the message passes the filters and handles it if so.

        This method overrides the check method from MessageHandler to add locale handling.
        It sets the locale for the response based on the message's origin before proceeding with
        the usual checks and handling.

        Parameters
        ----------
        client : Client
            The client instance.
        message : Message
            The message to check and potentially handle.

        Returns
        -------
        None | Callable
            The handler's callback function if the message passes the filters and is to be
            processed, None otherwise.
        """
        locale = await self._get_locale(message)
        with i18n.context(), i18n.use_locale(locale):
            if await self._check(client, message):
                return await self._handle_update(client, message)
        return None

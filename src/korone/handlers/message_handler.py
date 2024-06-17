# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>


from hydrogram import Client
from hydrogram.handlers import MessageHandler
from hydrogram.types import Message

from korone.handlers.base import BaseHandler


class KoroneMessageHandler(MessageHandler, BaseHandler):
    """
    A handler for processing messages in the Korone.

    This class inherits from both MessageHandler and BaseHandler to provide a specialized handler
    for processing messages. It integrates locale handling based on the message's origin, allowing
    for localized responses.
    """

    async def check(self, client: Client, message: Message) -> None:
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
        return await self._check_and_handle(client, message)

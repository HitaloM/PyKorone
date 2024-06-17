# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>


from hydrogram import Client
from hydrogram.handlers import CallbackQueryHandler
from hydrogram.types import CallbackQuery

from korone.handlers.base import BaseHandler


class KoroneCallbackQueryHandler(CallbackQueryHandler, BaseHandler):
    """
    A handler for processing callback queries in the Korone.

    This class inherits from both CallbackQueryHandler and BaseHandler to provide a specialized
    handler for processing callback queries. It integrates locale handling based on the callback
    query's origin, allowing for localized responses.
    """

    async def check(self, client: Client, callback_query: CallbackQuery) -> None:
        """
        Checks if the callback query passes the filters and handles it if so.

        This method overrides the check method from CallbackQueryHandler to add locale handling.
        It sets the locale for the response based on the callback query's origin before proceeding
        with the usual checks and handling.

        Parameters
        ----------
        client : Client
            The client instance.
        callback_query : CallbackQuery
            The callback query to check and potentially handle.

        Returns
        -------
        None | Callable
            The handler's callback function if the callback query passes the filters and is to be
            processed, None otherwise.
        """
        return await self._check_and_handle(client, callback_query)

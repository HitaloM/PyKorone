# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from collections.abc import Callable

from hydrogram import Client
from hydrogram.filters import Filter
from hydrogram.handlers import CallbackQueryHandler
from hydrogram.types import CallbackQuery

from korone import i18n
from korone.handlers.base import BaseHandler


class KoroneCallbackQueryHandler(CallbackQueryHandler, BaseHandler):
    """
    A handler for processing callback queries in the Korone.

    This class inherits from both CallbackQueryHandler and BaseHandler to provide a specialized
    handler for processing callback queries. It integrates locale handling based on the callback
    query's origin, allowing for localized responses.

    Parameters
    ----------
    callback : Callable
        The callback function that will be called if the callback query passes the filters.
    filters : Filter | None, optional
        A filter object used to determine if a callback query should be processed by this handler.
    """

    __slots__ = ()

    def __init__(self, callback: Callable, filters: Filter | None = None) -> None:
        CallbackQueryHandler.__init__(self, callback, filters)  # type: ignore
        BaseHandler.__init__(self, callback, filters)

    async def check(self, client: Client, callback_query: CallbackQuery) -> None | Callable:
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
        locale = await self._get_locale(callback_query)
        with i18n.context(), i18n.use_locale(locale):
            if await self._check(client, callback_query):
                return await self._handle_update(client, callback_query)
        return None

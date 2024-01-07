# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from abc import ABC, abstractmethod

from hydrogram import Client
from hydrogram.types import CallbackQuery


class CallbackQueryHandler(ABC):
    """
    Abstract base class for callback query handlers.

    This class is an abstract base class for callback query handlers. It
    defines the interface for callback query handlers. All callback query
    handlers must inherit from this class.
    """

    @abstractmethod
    async def handle(self, client: Client, callback: CallbackQuery) -> None:
        """
        Handle a callback query.

        TThis method is called when a callback query is received. It takes
        a Client object and a CallbackQuery object as parameters and performs
        some action based on the callback query content or metadata. This method
        must be implemented by subclasses.

        Parameters
        ----------
        client : hydrogram.Client
            The client object representing the Telegram bot.
        callback : hydrogram.types.CallbackQuery
            The callback query object representing the received callback query.
        """
        ...

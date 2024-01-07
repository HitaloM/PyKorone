# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from abc import ABC, abstractmethod

from hydrogram import Client
from hydrogram.types import Message


class MessageHandler(ABC):
    """
    Abstract base class for message handlers.

    This class is an abstract base class for message handlers. It defines the
    interface for message handlers. All message handlers must inherit from
    this class.
    """

    @abstractmethod
    async def handle(self, client: Client, message: Message) -> None:
        """
        Handle a message.

        This method is called when a message is received. It takes a Client
        object and a Message object as parameters and performs some action
        based on the message content or metadata. This method must be
        implemented by subclasses.

        Parameters
        ----------
        client : hydrogram.Client
            The Client object representing the Telegram bot.
        message : hydrogram.types.Message
            The Message object that represents the message.
        """
        ...

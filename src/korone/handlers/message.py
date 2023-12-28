# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from abc import ABC, abstractmethod

from hydrogram import Client
from hydrogram.types import Message


class MessageHandler(ABC):
    """
    A MessageHandler is an abstract base class that defines the interface
    for handling messages in Pyrogram.

    Subclasses of MessageHandler must implement the handle method, which
    takes a Client and a Message object as parameters and performs some
    action based on the message content or metadata.

    Parameters
    ----------
    client : Client
        The Client object that received the message.
    message : Message
        The Message object that represents the message.
    """

    @abstractmethod
    async def handle(self, client: Client, message: Message):
        """
        The handle method is an abstract method that must be implemented
        by subclasses of MessageHandler.

        The handle method is called by the Client when a message that matches
        the filters of the MessageHandler is received. The handle method can
        perform any action based on the message, such as sending a reply,
        editing the message, deleting the message, etc.

        Parameters
        ----------
        client : Client
            The Client object that received the message.
        message : Message
            The Message object that represents the message.
        """
        pass

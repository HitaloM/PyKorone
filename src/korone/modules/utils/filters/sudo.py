# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.filters import Filter
from hydrogram.types import CallbackQuery, Message

from korone.config import ConfigManager


class IsSudo(Filter):
    """
    Check if the user is a sudoer.

    This filter checks if the user is authorized as a sudoer based on their user ID.

    Parameters
    ----------
    client : hydrogram.Client
        The client object used for communication.
    update : hydrogram.types.Message or hydrogram.types.Message
        The update object representing the incoming message or callback query.
    """

    __slots__ = ("client", "message")

    def __init__(self, client: Client, update: Message | CallbackQuery) -> None:
        self.sudoers = ConfigManager().get("korone", "SUDOERS")
        self.client = client
        self.update = update

    def __call__(self):
        """
        Check if the user is a sudoer.

        This method checks if the user is authorized as a sudoer based on their user ID.

        Returns
        -------
        bool
            True if the user is a sudoer, False otherwise.
        """
        update = self.update
        is_callback = isinstance(update, CallbackQuery)
        message = update.message if is_callback else update

        if message.from_user is None:
            return False

        return message.from_user.id in self.sudoers

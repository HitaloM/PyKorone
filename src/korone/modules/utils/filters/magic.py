# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.filters import Filter
from hydrogram.types import Update
from magic_filter import MagicFilter


class Magic(Filter):
    """
    Filter an update using MagicFilter.

    This filter uses the magic command to determine if the function should be
    executed, it receives the magic command as a parameter and returns a
    function that will be used to create the filter.

    Parameters
    ----------
    magic : magic_filter.MagicFilter
        The magic command to be used to determine if the function should be
        executed.

    Examples
    --------
    >>> from magic_filter import F
    >>> from hydrogram import Client
    >>> from hydrogram.types import Message
    >>> from korone.modules.utils.filters import Magic
    >>> from korone.decorators import router
    >>> @router.message(Magic(F.text == "/start"))
    >>> async def handle(client: Client, message: Message) -> None:
    >>>    await message.reply("Hello, world!")
    """

    __slots__ = ("magic",)

    def __init__(self, magic: MagicFilter) -> None:
        self.magic = magic

    @staticmethod
    def validate_magic(magic: MagicFilter) -> None:
        """
        Validate the magic command.

        This method validates the magic command, it receives the magic command
        as a parameter and raises an exception if the magic command is invalid.

        Parameters
        ----------
        magic : magic_filter.MagicFilter
            The magic command to be validated.

        Raises
        ------
        TypeError
            If the magic command is not an instance of MagicFilter.
        """
        if not isinstance(magic, MagicFilter):
            msg = "magic must be an instance of MagicFilter"
            raise TypeError(msg)

    def __call__(self, client: Client, update: Update) -> bool:
        """
        Execute the magic filter on the given update.

        This method executes the magic filter on the given update, it receives
        the client object and the update object as parameters and returns a
        boolean indicating if the update passes the magic filter.

        Parameters
        ----------
        client : hydrogram.Client
            The client object used to interact with the Telegram API.
        update : hydrogram.types.Update
            The update object representing the incoming message.

        Returns
        -------
        bool
            True if the update passes the magic filter, False otherwise.
        """
        self.validate_magic(self.magic)

        return self.magic.resolve(update)

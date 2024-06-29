# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from collections.abc import Generator

from hydrogram import Client
from hydrogram.enums import ChatType
from hydrogram.filters import Filter
from hydrogram.types import Message

from korone.utils.i18n import gettext as _


class IsPrivateChat(Filter):
    """
    Filter to check if the chat is a private chat.

    This filter checks if the chat is a private chat. It can be used to restrict access to certain
    commands or features.

    Parameters
    ----------
    client : hydrogram.Client
        The client instance used to interact with the Telegram Bot API.
    message : hydrogram.types.Message
        The update object representing the incoming message.
    """

    __slots__ = ("client", "message")

    def __init__(self, client: Client, message: Message) -> None:
        self.client = client
        self.message = message

    async def __call__(self) -> bool:
        """
        Check if the chat is a private chat.

        This method checks if the chat is a private chat. It can be used to restrict access to
        certain commands or features.

        Returns
        -------
        bool
            True if the chat is a private chat, False otherwise.
        """

        if self.message.chat.type != ChatType.PRIVATE:
            await self.message.reply_text(
                _("This command was designed to be used in PM, not in group chats!")
            )
            return False

        return True

    def __await__(self) -> Generator:
        """
        Allow the filter to be used in an await expression.

        This method allows the filter to be used in an await expression.
        It is needed because the :class:`hydrogram.filters.AndFilter` tries to call the filter
        object as a coroutine.

        Returns
        -------
        Awaitable[bool]
            An awaitable object that resolves to True if the user is an administrator,
            False otherwise.
        """
        return self.__call__().__await__()  # type: ignore


class IsGroupChat(Filter):
    """
    Filter to check if the chat is a group chat.

    This filter checks if the chat is a group chat. It can be used to restrict access to certain
    commands or features.

    Parameters
    ----------
    client : hydrogram.Client
        The client instance used to interact with the Telegram Bot API.
    message : hydrogram.types.Message
        The update object representing the incoming message.
    """

    __slots__ = ("client", "message")

    def __init__(self, client: Client, message: Message) -> None:
        self.client = client
        self.message = message

    async def __call__(self) -> bool:
        """
        Check if the chat is a group chat.

        This method checks if the chat is a group chat. It can be used to restrict access to
        certain commands or features.

        Returns
        -------
        bool
            True if the chat is a group chat, False otherwise.
        """

        if self.message.chat.type not in {ChatType.GROUP, ChatType.SUPERGROUP}:
            await self.message.reply_text(
                _("This command was designed to be used in group chats, not in PM!")
            )
            return False

        return True

    def __await__(self) -> Generator:
        """
        Allow the filter to be used in an await expression.

        This method allows the filter to be used in an await expression.
        It is needed because the :class:`hydrogram.filters.AndFilter` tries to call the filter
        object as a coroutine.

        Returns
        -------
        Awaitable[bool]
            An awaitable object that resolves to True if the user is an administrator,
            False otherwise.
        """
        return self.__call__().__await__()  # type: ignore

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

from collections.abc import Generator

from hydrogram import Client
from hydrogram.enums import ChatMemberStatus, ChatType
from hydrogram.filters import Filter
from hydrogram.types import CallbackQuery, Message


class IsAdmin(Filter):
    """
    Filter to check if a user is an administrator.

    This filter checks if a user is an administrator in a chat. It can be used to restrict access
    to certain commands or features.

    Parameters
    ----------
    client : hydrogram.Client
        The client instance used to interact with the Telegram Bot API.
    update : hydrogram.types.Message or hydrogram.types.CallbackQuery
        The update object representing the incoming message or callback query.
    """

    __slots__ = ("client", "update")

    def __init__(self, client: Client, update: Message | CallbackQuery) -> None:
        self.client = client
        self.update = update

    async def __call__(self) -> bool:
        """
        Check if the user is an administrator in the chat.

        This method checks if the user is an administrator in the chat. It can be used to restrict
        access to certain commands or features.

        Returns
        -------
        bool
            True if the user is an administrator, False otherwise.
        """
        update = self.update
        is_callback = isinstance(update, CallbackQuery)
        message = update.message if is_callback else update

        if message.from_user is None:
            return False

        if message.chat.type == ChatType.PRIVATE:
            return True

        user = await self.client.get_chat_member(message.chat.id, message.from_user.id)
        return user.status in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}

    def __await__(self) -> Generator:
        """
        Allow the IsAdmin filter to be used in an await expression.

        This method allows the IsAdmin filter to be used in an await expression.
        It is needed because the :class:`hydrogram.filters.AndFilter` tries  to call the filter
        object as a coroutine.

        Returns
        -------
        Awaitable[bool]
            An awaitable object that resolves to True if the user is an administrator,
            False otherwise.
        """
        return self.__call__().__await__()

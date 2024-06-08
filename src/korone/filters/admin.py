# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>


from hydrogram import Client
from hydrogram.enums import ChatMemberStatus, ChatType
from hydrogram.types import CallbackQuery, Message

from korone.filters.base import KoroneFilter


class IsAdmin(KoroneFilter):
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

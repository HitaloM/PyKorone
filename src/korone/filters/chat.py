# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from collections.abc import Generator
from typing import Any, Final

from hydrogram import Client
from hydrogram.enums import ChatType
from hydrogram.filters import Filter
from hydrogram.types import Message

from korone.utils.i18n import gettext as _


class ChatTypeFilter(Filter):
    """Filter messages based on chat type.

    This filter checks if a message is from a specific chat type
    (private, group, supergroup, or channel) and sends an error message
    if the condition is not met.

    Attributes:
        client: The client instance
        message: The message to check
        expected_types: Set of chat types that pass this filter
        error_message: Message to send if filter fails
    """

    __slots__ = ("client", "error_message", "expected_types", "message")

    def __init__(
        self, client: Client, message: Message, expected_types: set[ChatType], error_message: str
    ) -> None:
        """Initialize the chat type filter.

        Args:
            client: The client instance
            message: The message to check
            expected_types: Set of chat types that should pass this filter
            error_message: Message to reply with if filter fails
        """
        self.client = client
        self.message = message
        self.expected_types = expected_types
        self.error_message = error_message

    async def __call__(self) -> bool:
        """Check if the message is from an expected chat type.

        Returns:
            bool: True if message is from allowed chat type, False otherwise
        """
        if self.message.chat.type not in self.expected_types:
            await self.message.reply(self.error_message)
            return False
        return True

    def __await__(self) -> Generator[Any, Any, bool]:
        return self.__call__().__await__()


class IsPrivateChat(ChatTypeFilter):
    """Filter that only allows messages from private chats.

    This filter checks if a message is from a private chat and sends
    an error message if it's from any other chat type.
    """

    PRIVATE_CHAT_TYPES: Final[set[ChatType]] = {ChatType.PRIVATE}

    def __init__(self, client: Client, message: Message) -> None:
        """Initialize the private chat filter.

        Args:
            client: The client instance
            message: The message to check
        """
        super().__init__(
            client,
            message,
            expected_types=self.PRIVATE_CHAT_TYPES,
            error_message=_("This command is designed to be used in PM, not in groups!"),
        )


class IsGroupChat(ChatTypeFilter):
    """Filter that only allows messages from group chats.

    This filter checks if a message is from a group or supergroup chat
    and sends an error message if it's from any other chat type.
    """

    GROUP_CHAT_TYPES: Final[set[ChatType]] = {ChatType.GROUP, ChatType.SUPERGROUP}

    def __init__(self, client: Client, message: Message) -> None:
        """Initialize the group chat filter.

        Args:
            client: The client instance
            message: The message to check
        """
        super().__init__(
            client,
            message,
            expected_types=self.GROUP_CHAT_TYPES,
            error_message=_("This command is designed to be used in groups, not in PM!"),
        )

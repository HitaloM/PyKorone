# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from collections.abc import Generator
from typing import Any

from hydrogram import Client
from hydrogram.enums import ChatType
from hydrogram.filters import Filter
from hydrogram.types import Message

from korone.utils.i18n import gettext as _


class ChatTypeFilter(Filter):
    __slots__ = ("client", "error_message", "expected_types", "message")

    def __init__(
        self, client: Client, message: Message, expected_types: set[ChatType], error_message: str
    ) -> None:
        self.client = client
        self.message = message
        self.expected_types = expected_types
        self.error_message = error_message

    async def __call__(self) -> bool:
        if self.message.chat.type not in self.expected_types:
            await self.message.reply(self.error_message)
            return False
        return True

    def __await__(self) -> Generator[Any, Any, bool]:
        return self.__call__().__await__()


class IsPrivateChat(ChatTypeFilter):
    def __init__(self, client: Client, message: Message) -> None:
        super().__init__(
            client,
            message,
            expected_types={ChatType.PRIVATE},
            error_message=_("This command is designed to be used in PM, not in groups!"),
        )


class IsGroupChat(ChatTypeFilter):
    def __init__(self, client: Client, message: Message) -> None:
        super().__init__(
            client,
            message,
            expected_types={ChatType.GROUP, ChatType.SUPERGROUP},
            error_message=_("This command is designed to be used in groups, not in PM!"),
        )

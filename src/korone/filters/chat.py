# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from collections.abc import Generator
from typing import Any

from hydrogram import Client
from hydrogram.enums import ChatType
from hydrogram.filters import Filter
from hydrogram.types import Message

from korone.utils.i18n import gettext as _


class IsPrivateChat(Filter):
    __slots__ = ("client", "message")

    def __init__(self, client: Client, message: Message) -> None:
        self.client = client
        self.message = message

    async def __call__(self) -> bool:
        if self.message.chat.type != ChatType.PRIVATE:
            await self.message.reply(
                _("This command was designed to be used in PM, not in group chats!")
            )
            return False

        return True

    def __await__(self) -> Generator[Any, Any, bool]:
        return self.__call__().__await__()


class IsGroupChat(Filter):
    __slots__ = ("client", "message")

    def __init__(self, client: Client, message: Message) -> None:
        self.client = client
        self.message = message

    async def __call__(self) -> bool:
        if self.message.chat.type not in {ChatType.GROUP, ChatType.SUPERGROUP}:
            await self.message.reply(
                _("This command was designed to be used in group chats, not in PM!")
            )
            return False

        return True

    def __await__(self) -> Generator[Any, Any, bool]:
        return self.__call__().__await__()

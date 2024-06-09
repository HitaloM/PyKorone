# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from collections.abc import Callable

from hydrogram import Client
from hydrogram.filters import Filter
from hydrogram.handlers import MessageHandler
from hydrogram.types import Message

from korone import i18n
from korone.handlers.base import BaseHandler


class KoroneMessageHandler(MessageHandler, BaseHandler):
    __slots__ = ()

    def __init__(self, callback: Callable, filters: Filter | None = None) -> None:
        MessageHandler.__init__(self, callback, filters)  # type: ignore
        BaseHandler.__init__(self, callback, filters)

    async def check(self, client: Client, message: Message) -> None | Callable:
        locale = await self._get_locale(message)
        with i18n.context(), i18n.use_locale(locale):
            if await self._check(client, message):
                return await self._handle_update(client, message)
        return None

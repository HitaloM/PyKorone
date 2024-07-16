# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.handlers import MessageHandler
from hydrogram.types import Message

from korone.handlers.base import BaseHandler


class KoroneMessageHandler(MessageHandler, BaseHandler):
    async def check(self, client: Client, message: Message) -> None:
        return await self._check_and_handle(client, message)

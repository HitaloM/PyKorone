# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from __future__ import annotations

from typing import TYPE_CHECKING

from hydrogram.handlers import MessageHandler

from .base import BaseHandler

if TYPE_CHECKING:
    from hydrogram import Client
    from hydrogram.types import Message


class KoroneMessageHandler(MessageHandler, BaseHandler):
    async def check(self, client: Client, message: Message) -> None:
        return await self._check_and_handle(client, message)

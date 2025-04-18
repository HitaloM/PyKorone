# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from __future__ import annotations

from typing import TYPE_CHECKING

from hydrogram.handlers import MessageHandler

from .base import BaseHandler

if TYPE_CHECKING:
    from hydrogram import Client
    from hydrogram.types import Message


class KoroneMessageHandler(MessageHandler, BaseHandler):
    async def check(self, client: Client, message: Message) -> None:
        """Check and handle message updates.

        Args:
            client: The Hydrogram client.
            message: The message object to process.

        Returns:
            bool: True if message was handled, False otherwise.
        """
        return await self._check_and_handle(client, message)

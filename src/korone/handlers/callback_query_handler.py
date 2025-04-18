# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from __future__ import annotations

from typing import TYPE_CHECKING

from hydrogram.handlers import CallbackQueryHandler

from .base import BaseHandler

if TYPE_CHECKING:
    from hydrogram import Client
    from hydrogram.types import CallbackQuery


class KoroneCallbackQueryHandler(CallbackQueryHandler, BaseHandler):
    async def check(self, client: Client, callback: CallbackQuery) -> None:
        """Check and handle callback query updates.

        Args:
            client: The Hydrogram client.
            callback: The callback query to process.

        Returns:
            bool: True if callback was handled, False otherwise.
        """
        return await self._check_and_handle(client, callback)

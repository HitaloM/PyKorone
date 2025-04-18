# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from __future__ import annotations

from typing import TYPE_CHECKING

from hydrogram.handlers import ErrorHandler

from korone.utils.i18n import i18n

from .base import BaseHandler

if TYPE_CHECKING:
    from hydrogram import Client
    from hydrogram.types import Update


class KoroneErrorHandler(ErrorHandler, BaseHandler):
    async def check(self, client: Client, update: Update, exception: Exception) -> bool:
        """Check if exception should be handled and process it with proper locale.

        Args:
            client: The Hydrogram client.
            update: The update that caused the exception.
            exception: The exception that was raised.

        Returns:
            bool: True if exception was handled, False otherwise.
        """
        if not isinstance(exception, self.exceptions):
            return False

        locale = await self._fetch_locale(update)
        with i18n.context(), i18n.use_locale(locale):
            await self.callback(client, update, exception)
            return True

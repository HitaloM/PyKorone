# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.handlers import ErrorHandler
from hydrogram.types import Update

from korone.utils.i18n import i18n

from .base import BaseHandler


class KoroneErrorHandler(ErrorHandler, BaseHandler):
    async def check(self, client: Client, update: Update, exception: Exception) -> bool:
        if not isinstance(exception, self.exceptions):
            return False

        locale = await self._fetch_locale(update)
        with i18n.context(), i18n.use_locale(locale):
            await self.callback(client, update, exception)
            return True

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from hydrogram import Client
from hydrogram.handlers import CallbackQueryHandler
from hydrogram.types import CallbackQuery

from korone.handlers.base import BaseHandler


class KoroneCallbackQueryHandler(CallbackQueryHandler, BaseHandler):
    async def check(self, client: Client, callback_query: CallbackQuery) -> None:
        return await self._check_and_handle(client, callback_query)

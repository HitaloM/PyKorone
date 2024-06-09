# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from collections.abc import Callable

from hydrogram import Client
from hydrogram.filters import Filter
from hydrogram.handlers import CallbackQueryHandler
from hydrogram.types import CallbackQuery

from korone import i18n
from korone.handlers.base import BaseHandler


class KoroneCallbackQueryHandler(CallbackQueryHandler, BaseHandler):
    __slots__ = ()

    def __init__(self, callback: Callable, filters: Filter | None = None) -> None:
        CallbackQueryHandler.__init__(self, callback, filters)  # type: ignore
        BaseHandler.__init__(self, callback, filters)

    async def check(self, client: Client, callback_query: CallbackQuery) -> None | Callable:
        locale = await self._get_locale(callback_query)
        with i18n.context(), i18n.use_locale(locale):
            if await self._check(client, callback_query):
                return await self._handle_update(client, callback_query)
        return None

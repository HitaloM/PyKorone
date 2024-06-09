# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import inspect
from collections.abc import Callable

from hydrogram import Client
from hydrogram.enums import ChatType
from hydrogram.filters import Filter
from hydrogram.types import CallbackQuery, Message, Update, User

from korone import i18n
from korone.handlers.database import ChatManager, LanguageManager


class BaseHandler:
    __slots__ = ("callback", "chat_manager", "filters", "language_manager")

    def __init__(self, callback: Callable, filters: Filter | None = None) -> None:
        self.callback = callback
        self.filters = filters
        self.chat_manager = ChatManager()
        self.language_manager = LanguageManager()

    @staticmethod
    async def _get_message_and_user_from_update(
        update: Update,
    ) -> tuple[Message, User]:
        if isinstance(update, CallbackQuery):
            return update.message, update.from_user
        if isinstance(update, Message):
            return update, update.from_user
        msg = f"Invalid update type: {type(update)}"
        raise ValueError(msg)

    async def _get_locale(self, update: Update) -> str:
        message, user = await self._get_message_and_user_from_update(update)
        chat = message.chat

        if user and chat.type == ChatType.PRIVATE:
            return await self.language_manager.get_locale(user)
        if chat.type in {ChatType.GROUP, ChatType.SUPERGROUP}:
            return await self.language_manager.get_locale(chat)
        return i18n.default_locale

    async def _handle_update(self, client: Client, update: Update) -> Callable | None:
        try:
            message, user = await self._get_message_and_user_from_update(update)
        except ValueError:
            return None

        if isinstance(update, CallbackQuery):
            await self.chat_manager.save_from_user(user)
        else:  # Message
            await self.chat_manager.handle_message(message)

        if user and not user.is_bot and message:
            return await self.callback(client, update)

        return None

    async def _check(self, client: Client, update: Update) -> bool:
        try:
            message, _ = await self._get_message_and_user_from_update(update)
        except ValueError:
            return False

        if not message or not callable(self.filters):
            return False

        if inspect.iscoroutinefunction(self.filters.__call__):
            return await self.filters(client, update)
        return await client.loop.run_in_executor(client.executor, self.filters, client, update)  # type: ignore

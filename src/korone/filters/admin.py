# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from collections.abc import Generator
from typing import Any

from hydrogram import Client
from hydrogram.enums import ChatMemberStatus, ChatType
from hydrogram.filters import Filter
from hydrogram.types import CallbackQuery, Message

from korone.utils.i18n import gettext as _


class IsAdmin(Filter):
    __slots__ = ("client", "show_alert", "update")

    def __init__(
        self, client: Client, update: Message | CallbackQuery, *, show_alert: bool = True
    ) -> None:
        self.client = client
        self.update = update
        self.show_alert = show_alert

    async def __call__(self) -> bool:
        update = self.update
        is_callback = isinstance(update, CallbackQuery)
        message = update.message if is_callback else update
        user = update.from_user if is_callback else message.from_user

        if not user:
            return False

        if message.chat.type == ChatType.PRIVATE:
            return True

        chat_member = await self.client.get_chat_member(message.chat.id, user.id)
        if chat_member.status in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}:
            return True

        if self.show_alert:
            alert_text = _("You must be an administrator to use this.")
            if is_callback:
                await update.answer(text=alert_text, show_alert=True, cache_time=60)
            else:
                await message.reply(alert_text)

        return False

    def __await__(self) -> Generator[Any, Any, bool]:
        return self.__call__().__await__()

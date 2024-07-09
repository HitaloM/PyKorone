# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from collections.abc import Generator

from hydrogram import Client
from hydrogram.enums import ChatMemberStatus, ChatType
from hydrogram.filters import Filter
from hydrogram.types import CallbackQuery, Message

from korone.utils.i18n import gettext as _


class IsAdmin(Filter):
    __slots__ = ("client", "update")

    def __init__(self, client: Client, update: Message | CallbackQuery) -> None:
        self.client = client
        self.update = update

    async def __call__(self) -> bool:
        update = self.update
        is_callback = isinstance(update, CallbackQuery)
        message = update.message if is_callback else update
        user = update.from_user if is_callback else message.from_user

        if not user:
            return False

        if message.chat.type == ChatType.PRIVATE:
            return True

        user = await self.client.get_chat_member(message.chat.id, user.id)
        if user.status in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}:
            return True

        if is_callback:
            await update.answer(
                text=_("You must be an administrator to use this."),
                show_alert=True,
                cache_time=60,
            )
        else:
            await message.reply(_("You must be an administrator to use this."))

        return False

    def __await__(self) -> Generator:
        return self.__call__().__await__()  # type: ignore

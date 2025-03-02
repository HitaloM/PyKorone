# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

from collections.abc import Generator
from typing import Any

from hydrogram import Client
from hydrogram.enums import ChatMemberStatus, ChatType
from hydrogram.errors import ChatAdminRequired
from hydrogram.filters import Filter
from hydrogram.types import CallbackQuery, ChatPrivileges, Message

from korone.utils.i18n import gettext as _


class AdminFilter(Filter):
    __slots__ = ("client", "permissions", "show_alert", "update")

    def __init__(
        self,
        client: Client,
        update: Message | CallbackQuery,
        permissions: ChatPrivileges | None = None,
        show_alert: bool = True,
    ) -> None:
        self.client = client
        self.update = update
        self.show_alert = show_alert
        self.permissions = permissions

    async def check_admin(self, user_id: int) -> bool:
        try:
            chat = (
                self.update.message.chat
                if isinstance(self.update, CallbackQuery)
                else self.update.chat
            )
            chat_member = await chat.get_member(user_id)
            return chat_member.status in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}
        except ChatAdminRequired:
            return False

    async def __call__(self) -> bool:
        update = self.update
        is_callback = isinstance(update, CallbackQuery)
        message = update.message if is_callback else update
        user = update.from_user if is_callback else message.from_user

        if not user:
            return False

        if message.chat.type == ChatType.PRIVATE:
            return True

        user_id = user.id if isinstance(self, UserIsAdmin) else self.client.me.id  # type: ignore
        is_admin = await self.check_admin(user_id)

        if is_admin:
            if isinstance(self, BotIsAdmin) and self.permissions:
                bot_member = await message.chat.get_member(self.client.me.id)  # type: ignore
                missing_perms = [
                    perm
                    for perm, value in self.permissions.__dict__.items()
                    if value and not getattr(bot_member.privileges, perm)
                ]
                if missing_perms:
                    if self.show_alert:
                        msg = _("I am missing the following permissions: {permissions}").format(
                            permissions=", ".join(missing_perms)
                        )
                        if is_callback:
                            await update.answer(msg, show_alert=True)
                        else:
                            await message.reply_text(msg)
                    return False
            return True

        if self.show_alert:
            alert_text = (
                _("You must be an administrator to use this.")
                if isinstance(self, UserIsAdmin)
                else _("I need to be an administrator to perform this action.")
            )
            if is_callback:
                await update.answer(text=alert_text, show_alert=True, cache_time=60)
            else:
                await message.reply(alert_text)

        return False

    def __await__(self) -> Generator[Any, Any, bool]:
        return self.__call__().__await__()


class UserIsAdmin(AdminFilter):
    pass


class BotIsAdmin(AdminFilter):
    pass

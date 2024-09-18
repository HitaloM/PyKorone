# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

from collections.abc import Generator
from typing import Any

from hydrogram import Client
from hydrogram.enums import ChatMemberStatus, ChatType
from hydrogram.filters import Filter
from hydrogram.types import CallbackQuery, ChatPrivileges, Message

from korone.utils.i18n import gettext as _


class UserIsAdmin(Filter):
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

        chat_member = await message.chat.get_member(user.id)
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


class BotIsAdmin(Filter):
    __slots__ = ("client", "permissions", "show_alert", "update")

    def __init__(
        self,
        client: Client,
        update: Message | CallbackQuery,
        *,
        permissions: ChatPrivileges | None = None,
        show_alert: bool = True,
    ) -> None:
        self.client = client
        self.update = update
        self.show_alert = show_alert
        self.permissions = permissions

    async def __call__(self) -> bool:
        update = self.update
        is_callback = isinstance(update, CallbackQuery)
        message = update.message if is_callback else update

        if message.chat.type == ChatType.PRIVATE:
            return True

        bot_member = await message.chat.get_member(self.client.me.id)  # type: ignore
        if bot_member.status in {ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER}:
            if not self.permissions or bot_member.status == ChatMemberStatus.OWNER:
                return True

            missing_perms = [
                perm
                for perm, value in self.permissions.__dict__.items()
                if value and not getattr(bot_member.privileges, perm)
            ]

            if not missing_perms:
                return True

            if self.show_alert:
                msg = _("I'm missing the following permissions: {permissions}").format(
                    permissions=", ".join(missing_perms)
                )
                if is_callback:
                    await update.answer(msg, show_alert=True)
                else:
                    await message.reply_text(msg)
            return False

        if self.show_alert:
            alert_text = _("I must be an administrator to do this.")
            if is_callback:
                await update.answer(text=alert_text, show_alert=True, cache_time=60)
            else:
                await message.reply(alert_text)

        return False

    def __await__(self) -> Generator[Any, Any, bool]:
        return self.__call__().__await__()

from __future__ import annotations

from datetime import timedelta
from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import Message
from ass_tg.types import ActionTimeArg, OptionalArg, TextArg
from ass_tg.types.base_abc import ArgFabric
from babel.dates import format_timedelta
from stfu_tg import KeyValue, Section, UserLink

from sophie_bot.args.users import SophieUserArg
from sophie_bot.config import CONFIG
from sophie_bot.filters.admin_rights import BotHasPermissions, UserRestricting
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.utils_.admin import is_user_admin
from sophie_bot.modules.restrictions.utils.restrictions import mute_user
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.modules.utils_.get_user import get_arg_or_reply_user, get_union_user
from sophie_bot.modules.utils_.message import is_real_reply
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Mutes the user in the chat."))
class MuteUserHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (
            CMDFilter("mute"),
            UserRestricting(can_restrict_members=True),
            BotHasPermissions(can_restrict_members=True),
        )

    @classmethod
    async def handler_args(cls, message: Message | None, data: dict) -> dict[str, ArgFabric]:
        args: dict[str, ArgFabric] = {}

        if not message or not is_real_reply(message):
            args["user"] = SophieUserArg(l_("User"))

        args["reason"] = OptionalArg(TextArg(l_("Reason")))

        return args

    async def handle(self) -> Any:
        connection = self.connection

        if not self.event.from_user:
            raise SophieException("No from_user")

        user = get_union_user(get_arg_or_reply_user(self.event, self.data))

        if user.chat_id == CONFIG.bot_id:
            return await self.event.reply(_("I cannot mute myself."))

        if self.event.from_user and user.chat_id == self.event.from_user.id:
            return await self.event.reply(_("You cannot mute yourself."))

        if await is_user_admin(connection.tid, user.chat_id):
            return await self.event.reply(_("I cannot mute an admin."))

        if not await mute_user(connection.tid, user.chat_id):
            return await self.event.reply(_("Failed to mute the user. Make sure I have the right permissions."))

        reason = self.data.get("reason")

        doc = Section(
            KeyValue(_("Chat"), connection.title),
            KeyValue(_("User"), UserLink(user.chat_id, user.first_name)),
            KeyValue(_("Muted by"), UserLink(self.event.from_user.id, self.event.from_user.first_name)),
            KeyValue(_("Reason"), reason) if reason else None,
            title=_("User muted"),
        )

        await self.event.reply(str(doc))


@flags.help(description=l_("Temporarily mutes the user in the chat."))
class TempMuteUserHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (
            CMDFilter("tmute"),
            UserRestricting(can_restrict_members=True),
            BotHasPermissions(can_restrict_members=True),
        )

    @classmethod
    async def handler_args(cls, message: Message | None, data: dict) -> dict[str, ArgFabric]:
        args: dict[str, ArgFabric] = {}

        if not message or not is_real_reply(message):
            args["user"] = SophieUserArg(l_("User"))

        args["time"] = ActionTimeArg(l_("Time (e.g., 2h, 7d, 2w)"))
        args["reason"] = OptionalArg(TextArg(l_("Reason")))

        return args

    async def handle(self) -> Any:
        connection = self.connection

        if not self.event.from_user:
            raise SophieException("No from_user")

        user = get_union_user(get_arg_or_reply_user(self.event, self.data))

        if user.chat_id == CONFIG.bot_id:
            return await self.event.reply(_("I cannot mute myself."))

        if self.event.from_user and user.chat_id == self.event.from_user.id:
            return await self.event.reply(_("You cannot mute yourself."))

        if await is_user_admin(connection.tid, user.chat_id):
            return await self.event.reply(_("I cannot mute an admin."))

        until_date: timedelta = self.data["time"]

        if not await mute_user(connection.tid, user.chat_id, until_date=until_date):
            return await self.event.reply(_("Failed to mute the user. Make sure I have the right permissions."))

        reason = self.data.get("reason")

        doc = Section(
            KeyValue(_("Chat"), connection.title),
            KeyValue(_("User"), UserLink(user.chat_id, user.first_name)),
            KeyValue(_("Muted by"), UserLink(self.event.from_user.id, self.event.from_user.first_name)),
            KeyValue(_("Duration"), format_timedelta(until_date, locale=self.current_locale)),
            KeyValue(_("Reason"), reason) if reason else None,
            title=_("User temporarily muted"),
        )

        await self.event.reply(str(doc))

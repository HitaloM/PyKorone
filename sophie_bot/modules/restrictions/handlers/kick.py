from __future__ import annotations

from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import Message
from ass_tg.types import OptionalArg, TextArg
from ass_tg.types.base_abc import ArgFabric
from stfu_tg import KeyValue, Section, UserLink

from sophie_bot.args.users import SophieUserArg
from sophie_bot.config import CONFIG
from sophie_bot.filters.admin_rights import BotHasPermissions, UserRestricting
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.logging.events import LogEvent
from sophie_bot.modules.logging.utils import log_event
from sophie_bot.modules.utils_.admin import is_user_admin
from sophie_bot.modules.restrictions.utils.restrictions import kick_user
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.modules.utils_.get_user import get_arg_or_reply_user, get_union_user
from sophie_bot.modules.utils_.message import is_real_reply
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Kicks the user from the chat. The user would be able to join back."))
class KickUserHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (
            CMDFilter("kick"),
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
            return await self.event.reply(_("I cannot kick myself."))

        if self.event.from_user and user.chat_id == self.event.from_user.id:
            return await self.event.reply(_("You cannot kick yourself."))

        if await is_user_admin(connection.tid, user.chat_id):
            return await self.event.reply(_("I cannot kick an admin."))

        if not await kick_user(connection.tid, user.chat_id):
            return await self.event.reply(_("Failed to kick the user. Make sure I have the right permissions."))

        reason = self.data.get("reason")
        await log_event(
            connection.tid,
            self.event.from_user.id,
            LogEvent.USER_KICKED,
            {"target_user_id": user.chat_id, "reason": reason},
        )

        doc = Section(
            KeyValue(_("Chat"), connection.title),
            KeyValue(_("User"), UserLink(user.chat_id, user.first_name)),
            KeyValue(_("Kicked by"), UserLink(self.event.from_user.id, self.event.from_user.first_name)),
            KeyValue(_("Reason"), reason) if reason else None,
            title=_("User kicked"),
        )

        await self.event.reply(str(doc))

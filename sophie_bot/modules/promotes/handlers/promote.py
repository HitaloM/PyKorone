from typing import Any, Optional

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
from sophie_bot.modules.legacy_modules.utils.user_details import get_admins_rights
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.modules.utils_.get_user import get_arg_or_reply_user, get_union_user
from sophie_bot.modules.utils_.message import is_real_reply
from sophie_bot.services.bot import bot
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Promotes the user to admins."))
class PromoteUserHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (
            CMDFilter("promote"),
            UserRestricting(can_promote_members=True),
            BotHasPermissions(can_promote_members=True),
        )

    @classmethod
    async def handler_args(cls, message: Message | None, data: dict) -> dict[str, ArgFabric]:
        args = {}

        if not message or not is_real_reply(message):
            args["user"] = SophieUserArg(l_("User"))

        args["admin_title"] = OptionalArg(TextArg(l_("?Admin title")))

        return args

    async def handle(self) -> Any:
        connection = self.connection

        admin_title: Optional[str] = self.data.get("admin_title")

        if not self.event.from_user:
            raise SophieException("No from_user")

        user = get_union_user(get_arg_or_reply_user(self.event, self.data))

        if user.chat_id == CONFIG.bot_id:
            return await self.event.reply(_("I cannot promote myself."))

        elif self.event.from_user and user.chat_id == self.event.from_user.id:
            return await self.event.reply(_("You cannot promote yourself."))

        if admin_title and len(admin_title) > 16:
            return await self.event.reply(_("Admin title is too long."))

        await bot.promote_chat_member(
            chat_id=connection.tid,
            user_id=user.chat_id,
            can_invite_users=True,
            can_change_info=True,
            can_restrict_members=True,
            can_delete_messages=True,
            can_pin_messages=True,
            can_delete_stories=True,
        )

        if admin_title:
            await bot.set_chat_administrator_custom_title(
                chat_id=connection.tid, user_id=user.chat_id, custom_title=admin_title
            )

        # Reset admin cache
        await get_admins_rights(connection.tid, force_update=True)

        doc = Section(
            KeyValue(_("Chat"), connection.title),
            KeyValue(_("User"), UserLink(user.chat_id, user.first_name)),
            KeyValue(_("Promoted by"), UserLink(self.event.from_user.id, self.event.from_user.first_name)),
            KeyValue(_("Admin title"), admin_title) if admin_title else _("No admin title"),
            title=_("Admin promoted successfully"),
        )

        await self.event.reply(str(doc))

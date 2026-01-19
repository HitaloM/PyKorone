from ass_tg.types.base_abc import ArgFabric
from sophie_bot.config import CONFIG
from typing import Optional

from aiogram import flags
from aiogram.types import Message
from ass_tg.types import TextArg, OptionalArg
from stfu_tg import Doc, Title, Section, KeyValue, UserLink

from sophie_bot.args.users import SophieUserArg
from sophie_bot.db.models import ChatModel
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.modules.warns.utils import warn_user
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_
from sophie_bot.modules.utils_.admin import is_user_admin
from sophie_bot.filters.admin_rights import BotHasPermissions, UserRestricting


@flags.help(description=l_("Warns a user."))
@flags.disableable(name="warn")
class WarnHandler(SophieMessageHandler):
    @staticmethod
    def filters():
        return (
            CMDFilter("warn"),
            UserRestricting(can_restrict_members=True),
            BotHasPermissions(can_restrict_members=True),
        )

    @classmethod
    async def handler_args(cls, message: Message | None, data: dict) -> dict[str, ArgFabric]:
        return {
            "user": SophieUserArg(l_("User to warn")),
            "reason": OptionalArg(TextArg(l_("Reason"))),
        }

    async def handle(self):
        message: Message = self.event
        target_user: ChatModel = self.data["user"]
        admin_user: ChatModel = self.data["user_db"]
        reason: Optional[str] = self.data["reason"]

        if target_user.tid == CONFIG.bot_id:
            await message.reply(_("I cannot warn myself."))
            return

        if await is_user_admin(self.connection.db_model.iid, target_user.iid):
            await message.reply(_("I cannot warn an admin."))
            return

        if not message.from_user:
            return

        current, limit, punishment = await warn_user(self.connection.db_model, target_user, admin_user, reason)

        # Construct response
        doc = Doc(
            Title(_("User Warned")),
            KeyValue(_("User"), UserLink(target_user.tid, target_user.first_name_or_title)),
            KeyValue(_("Admin"), UserLink(message.from_user.id, message.from_user.first_name)),
            KeyValue(_("Count"), f"{current}/{limit}"),
        )

        if reason:
            doc += Section(reason, title=_("Reason"))

        if punishment:
            doc += Section(_("User has been {punishment} due to reaching max warns.").format(punishment=punishment))

        await message.reply(str(doc))

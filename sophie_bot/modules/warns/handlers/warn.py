from ass_tg.types.base_abc import ArgFabric
from sophie_bot.config import CONFIG
from typing import Optional

from aiogram import flags
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from ass_tg.types import TextArg, OptionalArg
from stfu_tg import Doc, Title, Section, KeyValue, UserLink, Italic

from sophie_bot.args.users import SophieUserArg
from sophie_bot.db.models import ChatModel, RulesModel
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.modules.warns.utils import warn_user
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_
from sophie_bot.modules.utils_.admin import is_user_admin
from sophie_bot.filters.admin_rights import BotHasPermissions, UserRestricting
from sophie_bot.modules.logging.events import LogEvent
from sophie_bot.modules.logging.utils import log_event
from ..callbacks import DeleteWarnCallback


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

        current, limit, punishment, warn = await warn_user(self.connection.db_model, target_user, admin_user, reason)

        await log_event(
            self.connection.tid,
            message.from_user.id,
            LogEvent.WARN_ADDED,
            {"target_user_id": target_user.tid, "reason": reason, "current": current, "limit": limit},
        )

        # Construct response
        doc = Doc(
            Title(_("⚠️ User warned")),
            KeyValue(_("User"), UserLink(target_user.tid, target_user.first_name_or_title)),
            KeyValue(_("By admin"), UserLink(message.from_user.id, message.from_user.first_name)),
            KeyValue(_("Warnings count"), f"{current}/{limit}"),
        )

        if reason:
            doc += Section(Italic(reason), title=_("Reason"))

        if punishment:
            doc += Section(_("User has been {punishment} due to reaching max warns.").format(punishment=punishment))

        # Buttons
        builder = InlineKeyboardBuilder()

        # Rules button
        if await RulesModel.get_rules(message.chat.id):
            bot_username = (await self.bot.get_me()).username
            builder.row(
                InlineKeyboardButton(
                    text=f"🪧 {_('Rules')}",
                    url=f"https://t.me/{bot_username}?start=btn_rules_{message.chat.id}",
                )
            )

        # Delete warn button
        if not punishment and warn and warn.id:
            builder.row(
                InlineKeyboardButton(
                    text=f"🗑️ {_('Delete warn')}",
                    callback_data=DeleteWarnCallback(warn_iid=warn.id).pack(),
                )
            )

        await message.reply(str(doc), reply_markup=builder.as_markup())

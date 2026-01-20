from typing import Any

from aiogram import flags
from aiogram.types import Message
from stfu_tg import Doc, Bold, Template, UserLink, KeyValue, Section, VList

from sophie_bot.db.models import ChatModel, WarnModel, WarnSettingsModel
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.chat_status import ChatTypeFilter
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_
from .warns import optional_user


@flags.help(description=l_("Shows user's warns in the current chat."))
@flags.disableable(name="warns")
class WarnsGroupHandler(SophieMessageHandler):
    @staticmethod
    def filters():
        return CMDFilter("warns"), ~ChatTypeFilter("private")

    @classmethod
    async def handler_args(cls, message: Message | None, data: dict):
        return await optional_user(message, data)

    async def handle(self) -> Any:
        message: Message = self.event
        # Resolve target user
        if message.reply_to_message and message.reply_to_message.from_user:
            target_user_tid = message.reply_to_message.from_user.id
            target_user_name = message.reply_to_message.from_user.first_name
        elif "user" in self.data and self.data["user"]:
            target_user: ChatModel = self.data["user"]
            target_user_tid = target_user.tid
            target_user_name = target_user.first_name_or_title
        else:
            target_user_tid = message.from_user.id if message.from_user else 0
            target_user_name = message.from_user.first_name if message.from_user else _("Unknown")

        if not target_user_tid:
            return

        # Group: List warns in current chat
        chat_iid = self.connection.db_model.iid
        warns = await WarnModel.get_user_warns(chat_iid, target_user_tid)
        settings = await WarnSettingsModel.get_or_create(chat_iid)

        doc = Doc(Bold(Template(_("⚠️ Warnings for {user}"), user=UserLink(target_user_tid, target_user_name))))

        if warns:
            doc += KeyValue(_("Count"), f"{len(warns)}/{settings.max_warns}")
            reasons = [warn.reason or _("No reason provided") for warn in warns]
            doc += Section(VList(*reasons), title=_("Reasons"))

        else:
            doc += Section(_("The user has no warnings currently."))

        return await message.reply(doc.to_html())

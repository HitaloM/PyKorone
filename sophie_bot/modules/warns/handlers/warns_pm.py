from typing import Any

from aiogram import flags
from aiogram.types import Message
from stfu_tg import Doc, Title, KeyValue

from sophie_bot.db.models import ChatModel, WarnModel
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.chat_status import ChatTypeFilter
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Shows all your warns across all chats."))
class WarnsPMHandler(SophieMessageHandler):
    @staticmethod
    def filters():
        return CMDFilter("warns"), ChatTypeFilter("private")

    async def handle(self) -> Any:
        message: Message = self.event
        target_user_tid = message.from_user.id if message.from_user else 0

        if not target_user_tid:
            return

        # PM: List all warns across all chats
        warns = await WarnModel.find(WarnModel.user_id == target_user_tid).sort(WarnModel.date).to_list()

        if not warns:
            return await message.reply(_("You don't have warnings in any chat at the moment."))

        doc = Doc(Title(_("⚠️ Your warnings")))

        for warn in warns:
            chat = await ChatModel.get_by_iid(warn.chat.iid)
            chat_title = chat.title if chat else _("Unknown Chat")

            doc += KeyValue(chat_title, warn.reason or _("No reason provided"))

        return await message.reply(str(doc))

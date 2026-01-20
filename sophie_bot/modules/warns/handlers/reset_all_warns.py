from typing import Any

from aiogram import flags
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.chat_status import ChatTypeFilter
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_
from sophie_bot.modules.troubleshooters.callbacks import CallbackActionCancel
from ..callbacks import ResetAllWarnsCallback


@flags.help(description=l_("Resets all warnings of all users in the current chat."))
class ResetAllWarnsHandler(SophieMessageHandler):
    @staticmethod
    def filters():
        return (
            CMDFilter(("resetallwarns", "delallwarns")),
            ~ChatTypeFilter("private"),
            UserRestricting(can_restrict_members=True),
        )

    async def handle(self) -> Any:
        message: Message = self.event

        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text=_("Confirm"), callback_data=ResetAllWarnsCallback().pack()),
            InlineKeyboardButton(text=_("Cancel"), callback_data=CallbackActionCancel().pack()),
        )

        return await message.reply(
            _("Are you sure you want to reset ALL warnings in this chat?"), reply_markup=builder.as_markup()
        )

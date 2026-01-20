from typing import Any

from aiogram import flags
from aiogram.types import Message, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from stfu_tg import UserLink

from sophie_bot.db.models import ChatModel
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.filters.chat_status import ChatTypeFilter
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_
from sophie_bot.modules.troubleshooters.callbacks import CallbackActionCancel
from ..callbacks import ResetWarnsCallback
from .warns import optional_user


@flags.help(description=l_("Resets all warnings of a user in the current chat."))
class ResetWarnsHandler(SophieMessageHandler):
    @staticmethod
    def filters():
        return (
            CMDFilter(("resetwarns", "delwarns")),
            ~ChatTypeFilter("private"),
            UserRestricting(can_restrict_members=True),
        )

    @classmethod
    async def handler_args(cls, message: Message | None, data: dict):
        return await optional_user(message, data)

    async def handle(self) -> Any:
        message: Message = self.event
        if message.reply_to_message and message.reply_to_message.from_user:
            target_user_tid = message.reply_to_message.from_user.id
            target_user_name = message.reply_to_message.from_user.first_name
        elif "user" in self.data and self.data["user"]:
            target_user: ChatModel = self.data["user"]
            target_user_tid = target_user.tid
            target_user_name = target_user.first_name_or_title
        else:
            return await message.reply(_("Please provide a user to reset warns for."))

        builder = InlineKeyboardBuilder()
        builder.add(
            InlineKeyboardButton(text=_("Confirm"), callback_data=ResetWarnsCallback(user_tid=target_user_tid).pack()),
            InlineKeyboardButton(text=_("Cancel"), callback_data=CallbackActionCancel().pack()),
        )

        return await message.reply(
            _("Are you sure you want to reset warnings of {user}?").format(
                user=UserLink(target_user_tid, target_user_name)
            ),
            reply_markup=builder.as_markup(),
        )

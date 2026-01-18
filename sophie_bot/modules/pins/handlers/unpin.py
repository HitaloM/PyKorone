from __future__ import annotations

from aiogram import flags
from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message
from ass_tg.types import EqualsArg, OptionalArg

from sophie_bot.filters.admin_rights import BotHasPermissions, UserRestricting
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.services.bot import bot
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Unpins message"))
class UnpinHandler(SophieMessageHandler):
    @staticmethod
    def filters():
        return (
            CMDFilter(("unpin",)),
            UserRestricting(can_pin_messages=True),
            BotHasPermissions(can_pin_messages=True),
        )

    @classmethod
    async def handler_args(cls, message: Message | None, data: dict):
        return {
            "all": OptionalArg(EqualsArg("all")),
        }

    async def handle(self):
        message = self.event
        chat_id = message.chat.id

        if self.data["args"]["all"]:
            await bot.unpin_all_chat_messages(chat_id)
            return

        # If unpinning a specific message
        message_id = None
        if message.reply_to_message:
            message_id = message.reply_to_message.message_id

        try:
            await bot.unpin_chat_message(chat_id, message_id=message_id)
        except TelegramBadRequest as e:
            # Handle "chat not modified" or "message is not pinned"
            if "not modified" in str(e) or "not pinned" in str(e):
                await message.reply(_("The message is not pinned."))
            else:
                raise

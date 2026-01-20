from asyncio import sleep
from datetime import UTC, datetime, timedelta
from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType

from sophie_bot.filters.admin_rights import BotHasPermissions, UserRestricting
from sophie_bot.filters.chat_status import ChatTypeFilter
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.modules.logging.events import LogEvent
from sophie_bot.modules.logging.utils import log_event
from sophie_bot.modules.utils_.common_try import common_try
from sophie_bot.services.bot import bot
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Purges all messages after replied message (including the replied message)"))
class PurgeMessagesHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (
            CMDFilter("purge"),
            UserRestricting(admin=True, can_delete_messages=True),
            BotHasPermissions(can_delete_messages=True),
            ~ChatTypeFilter("private"),
        )

    async def handle(self) -> Any:
        if not self.event.from_user:
            return

        if not self.event.reply_to_message:
            return await self.event.reply(_("Reply to a message to start."))

        if self.event.date <= datetime.now(tz=UTC) - timedelta(days=2):
            return await self.event.reply(
                _(
                    "Couldn't delete the messages older than 48 hours (2 days). You can delete it nevertheless using the Telegram's admin tools."
                )
            )

        first = self.event.reply_to_message.message_id
        last = self.event.message_id

        chat_id = self.event.chat.id

        messages: list[int] = []
        for message_id in range(first - 1, last + 1):
            messages.append(message_id)

            if len(messages) == 100:
                await common_try(bot.delete_messages(chat_id, messages))
                messages = []

        await common_try(bot.delete_messages(chat_id, messages))

        count = last - first + 1
        await log_event(
            chat_id,
            self.event.from_user.id,
            LogEvent.MESSAGES_PURGED,
            {"count_approx": count},
        )

        msg = await bot.send_message(chat_id, _("Purge completed. This message will be removed in 5 seconds."))
        await sleep(5)
        await msg.delete()

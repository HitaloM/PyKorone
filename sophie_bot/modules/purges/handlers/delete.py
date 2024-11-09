from datetime import UTC, datetime, timedelta
from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType

from sophie_bot.filters.admin_rights import BotHasPermissions, UserRestricting
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Deletes the replied message"))
class DelMsgCmdHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (
            CMDFilter(("delete", "del")),
            UserRestricting(admin=True, can_delete_messages=True),
            BotHasPermissions(can_delete_messages=True),
        )

    async def handle(self) -> Any:
        if not self.event.reply_to_message:
            return await self.event.reply(_("Reply to a message to delete it."))

        if self.event.date <= (datetime.now(tz=UTC) - timedelta(days=2)):
            return await self.event.reply(
                _(
                    "Couldn't delete the message older than 48 hours (2 days). You can delete it nevertheless using the Telegram's admin tools."
                )
            )

        await self.event.delete()

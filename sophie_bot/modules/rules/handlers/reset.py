from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType

from sophie_bot.db.models import RulesModel
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.chat_status import ChatTypeFilter
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Resets chat rules to default settings."))
class ResetRulesHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter("resetrules"), ~ChatTypeFilter("private"), UserRestricting(admin=True)

    async def handle(self) -> Any:
        connection = self.connection

        await RulesModel.del_rules(connection.tid)
        await self.event.reply(_("🗑 Chat rules have been reset."))

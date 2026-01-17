from typing import Any

from aiogram import F, flags
from aiogram.dispatcher.event.handler import CallbackType

from sophie_bot.db.models import AIMemoryModel
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.ai.callbacks import AIResetContext
from sophie_bot.modules.ai.filters.ai_enabled import AIEnabledFilter
from sophie_bot.modules.ai.fsm.pm import AI_PM_RESET
from sophie_bot.modules.ai.utils.cache_messages import reset_messages
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Reset the chat's AI context and AI memory"))
class AIContextReset(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter("aireset"), UserRestricting(admin=True), AIEnabledFilter()

    @staticmethod
    def filters_alt() -> tuple[CallbackType, ...]:
        return F.text == AI_PM_RESET, UserRestricting(admin=True), AIEnabledFilter()

    @staticmethod
    def filters_callback() -> tuple[CallbackType, ...]:
        return AIResetContext.filter(), UserRestricting(admin=True), AIEnabledFilter()

    async def handle(self) -> Any:
        await reset_messages(self.connection.tid)

        if self.connection.db_model:
            await AIMemoryModel.clear(self.connection.db_model.iid)

        return await self.event.reply(
            _("🔄 AI context and AI memory was successfully reset. AI will now operate in a clean state.")
        )

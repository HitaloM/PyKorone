from typing import Any

from aiogram import F, flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.filters import or_f

from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.ai.callbacks import AIResetContext
from sophie_bot.modules.ai.filters.ai_enabled import AIEnabledFilter
from sophie_bot.modules.ai.fsm.pm import AI_PM_RESET
from sophie_bot.modules.ai.utils.cache_messages import reset_messages
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Reset the chat's AI context"))
class AIContextReset(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (or_f(CMDFilter("aireset"), F.text == AI_PM_RESET), UserRestricting(admin=True), AIEnabledFilter())

    @staticmethod
    def filters_callback() -> tuple[CallbackType, ...]:
        return AIResetContext.filter(), UserRestricting(admin=True), AIEnabledFilter()

    async def handle(self) -> Any:
        connection = self.connection()
        await reset_messages(connection.id)

        return await self.event.reply(
            _("🔄 AI context was successfully reset. AI will now operate in a clean " "state.")
        )

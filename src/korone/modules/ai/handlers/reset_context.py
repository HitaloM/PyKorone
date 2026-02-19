from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import F, flags

from korone.filters.admin_rights import UserRestricting
from korone.filters.chat_status import PrivateChatFilter
from korone.filters.cmd import CMDFilter
from korone.modules.ai.callbacks import AIResetContext
from korone.modules.ai.fsm.pm import AI_PM_RESET
from korone.modules.ai.utils.cache_messages import reset_messages
from korone.modules.ai.utils.memory import clear_memory
from korone.utils.handlers import KoroneMessageCallbackQueryHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram import Router


@flags.help(description=l_("Reset the chat AI context"))
class AIContextResetHandler(KoroneMessageCallbackQueryHandler):
    @classmethod
    def register(cls, router: Router) -> None:
        router.message.register(cls, CMDFilter("aireset"), UserRestricting(admin=True))
        router.message.register(cls, F.text == AI_PM_RESET, PrivateChatFilter())
        router.callback_query.register(cls, AIResetContext.filter(), UserRestricting(admin=True))

    async def handle(self) -> None:
        chat_id = self.message.chat.id
        await reset_messages(chat_id)
        await clear_memory(chat_id)
        await self.answer(_("🔄 AI context and AI memory were successfully reset."))

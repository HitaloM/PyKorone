from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram import flags

from korone.filters.admin_rights import UserRestricting
from korone.filters.chat_status import GroupChatFilter
from korone.filters.cmd import CMDFilter
from korone.modules.ai.utils.settings import is_ai_enabled, set_ai_enabled
from korone.modules.utils_.status_handler import StatusBoolHandlerABC
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@flags.help(description=l_("Enable or disable AI features in this chat."))
class AIEnableSettingsHandler(StatusBoolHandlerABC):
    header_text = l_("AI features")
    change_command = "enableai"
    change_args = l_("yes / no")

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter("enableai"), GroupChatFilter(notify_on_fail=True), UserRestricting(admin=True))

    async def get_status(self) -> bool:
        return await is_ai_enabled(self.chat.chat_id)

    async def set_status(self, *, new_status: bool) -> None:
        await set_ai_enabled(self.chat.chat_id, enabled=new_status)

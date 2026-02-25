from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.filters import Command

from korone.filters.admin_rights import UserRestricting
from korone.filters.chat_status import GroupChatFilter
from korone.modules.utils_.admin import get_admins_rights
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@flags.help(description=l_("Reset admin rights cache, use if Korone didn't get the recently added admin"))
class ResetAdminCache(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (Command("admincache"), UserRestricting(admin=True), GroupChatFilter(notify_on_fail=True))

    async def handle(self) -> None:
        await get_admins_rights(self.chat.chat_id, force_update=True)
        await self.event.reply(_("Admin rights cache has been reset."))

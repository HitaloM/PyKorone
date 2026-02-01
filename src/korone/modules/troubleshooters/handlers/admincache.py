from typing import TYPE_CHECKING

from aiogram import flags
from aiogram.enums import ChatType

from korone.filters.admin_rights import UserRestricting
from korone.filters.cmd import CMDFilter
from korone.modules.utils_.admin import get_admins_rights
from korone.modules.utils_.chat_member import update_chat_members
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_

if TYPE_CHECKING:
    from aiogram.dispatcher.event.handler import CallbackType


@flags.help(description=l_("Reset admin rights cache, use if Korone didn't get the recently added admin"))
class ResetAdminCache(KoroneMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter("admincache"), UserRestricting(admin=True))

    async def handle(self) -> None:
        if self.chat.type == ChatType.PRIVATE:
            await self.event.reply(_("You can't use this command in private chats."))
            return

        await get_admins_rights(self.chat.chat_id, force_update=True)
        await update_chat_members(self.chat.db_model)
        await self.event.reply(_("Admin rights cache has been reset."))

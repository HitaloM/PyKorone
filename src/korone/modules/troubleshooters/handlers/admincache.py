from typing import Any

from aiogram import flags

from korone.db.models.chat import ChatType
from korone.filters.admin_rights import UserRestricting
from korone.filters.cmd import CMDFilter
from korone.modules.utils_.admin import get_admins_rights
from korone.modules.utils_.chat_member import update_chat_members
from korone.utils.handlers import KoroneMessageHandler
from korone.utils.i18n import gettext as _
from korone.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Reset admin rights cache, use if Korone didn't get the recently added admin"))
class ResetAdminCache(KoroneMessageHandler):
    @staticmethod
    def filters():
        return (CMDFilter("admincache"), UserRestricting(admin=True))

    async def handle(self) -> Any:
        if self.chat.type == ChatType.private:
            return await self.event.reply(_("You can't use this command in private chats."))

        await get_admins_rights(self.chat.tid, force_update=True)
        await update_chat_members(self.chat.db_model)
        await self.event.reply(_("Admin rights cache has been reset."))

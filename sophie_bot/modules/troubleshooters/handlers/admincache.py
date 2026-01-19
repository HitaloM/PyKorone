from typing import Any

from aiogram import flags

from sophie_bot.db.models.chat import ChatType
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.utils_.admin import get_admins_rights
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.modules.utils_.chat_member import update_chat_members
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Reset admin rights cache, use if Sophie didn't get the recently added admin"))
class ResetAdminCache(SophieMessageHandler):
    @staticmethod
    def filters():
        return (CMDFilter("admincache"), UserRestricting(admin=True))

    async def handle(self) -> Any:
        # TODO: Make a flag for connection middleware
        if self.connection.type == ChatType.private:
            return await self.event.reply(_("You can't use this command in private chats."))

        await get_admins_rights(self.connection.tid, force_update=True)  # Reset a cache
        await update_chat_members(self.connection.db_model)
        await self.event.reply(_("Admin rights cache has been reset."))

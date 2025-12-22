from typing import Any

from aiogram import flags
from aiogram.handlers import MessageHandler

from sophie_bot.db.models.chat import ChatType
from sophie_bot.middlewares.connections import ChatConnection
from sophie_bot.modules.legacy_modules.utils.user_details import get_admins_rights
from sophie_bot.modules.utils_.user_details import update_chat_members
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Reset admin rights cache, use if Sophie didn't get the recently added admin"))
class ResetAdminCache(MessageHandler):
    async def handle(self) -> Any:
        chat: ChatConnection = self.data["connection"]

        # TODO: Make a flag for connection middleware
        if chat.type == ChatType.private:
            return await self.event.reply(_("You can't use this command in private chats."))

        await get_admins_rights(chat.id, force_update=True)  # Reset a cache
        await update_chat_members(chat.db_model)
        await self.event.reply(_("Admin rights cache has been reset."))

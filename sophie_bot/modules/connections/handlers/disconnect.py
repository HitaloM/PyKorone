from __future__ import annotations

from aiogram import flags
from aiogram.types import ReplyKeyboardRemove

from sophie_bot.modules.connections.utils.connection import set_connected_chat
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.utils.i18n import lazy_gettext as l_, gettext as _
from sophie_bot.filters.cmd import CMDFilter


@flags.help(description=l_("Disconnects from the current chat."))
class DisconnectCmd(SophieMessageHandler):
    @staticmethod
    def filters():
        return (CMDFilter("disconnect"),)

    async def handle(self):
        if not self.event.from_user:
            return

        user_id = self.event.from_user.id
        await set_connected_chat(user_id, None)
        await self.event.reply(_("Disconnected."), reply_markup=ReplyKeyboardRemove())

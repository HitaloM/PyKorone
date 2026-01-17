from stfu_tg import Template, Bold

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

        current_connection = self.connection

        if not current_connection.is_connected:
            await self.event.reply(
                _("You are not currently connected to any chat."),
                reply_markup=ReplyKeyboardRemove(),
            )
            return

        user_id = self.event.from_user.id
        await set_connected_chat(user_id, None)
        await self.event.reply(
            str(
                Template(
                    _("Successfully disconnected from the {chat_name} chat."), chat_name=Bold(current_connection.title)
                ).to_html()
            ),
            reply_markup=ReplyKeyboardRemove(),
        )

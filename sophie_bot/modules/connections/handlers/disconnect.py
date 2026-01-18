from aiogram.dispatcher.event.handler import CallbackType
from stfu_tg import Template, Bold

from aiogram import F, flags, Router
from aiogram.types import ReplyKeyboardRemove

from sophie_bot.filters.chat_status import ChatTypeFilter
from sophie_bot.modules.connections.utils.connection import set_connected_chat
from sophie_bot.modules.connections.utils.constants import CONNECTION_DISCONNECT_TEXT
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.utils.i18n import lazy_gettext as l_, gettext as _
from sophie_bot.filters.cmd import CMDFilter


@flags.help(description=l_("Disconnects from the current chat."))
class DisconnectCmd(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        # Defined in register
        return ()

    @classmethod
    def register(cls, router: Router):
        router.message.register(cls, CMDFilter("disconnect"), ChatTypeFilter("private"))
        router.message.register(cls, F.text == CONNECTION_DISCONNECT_TEXT, ChatTypeFilter("private"))

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

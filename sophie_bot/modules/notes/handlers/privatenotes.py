from typing import Any

from aiogram.dispatcher.event.handler import CallbackType
from stfu_tg import Bold, Doc, Template

from sophie_bot.middlewares.connections import ConnectionsMiddleware
from sophie_bot.modules.legacy_modules.utils.connections import set_connected_chat
from sophie_bot.modules.notes.callbacks import PrivateNotesStartUrlCallback
from sophie_bot.modules.notes.handlers.list import NotesList
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _


class PrivateNotesConnectHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (PrivateNotesStartUrlCallback.filter(),)

    async def handle(self) -> Any:
        if not self.event.from_user:
            return

        user_id = self.event.from_user.id
        command_start: PrivateNotesStartUrlCallback = self.data["command_start"]
        chat_id = command_start.chat_id

        # Connect to the chat
        await set_connected_chat(user_id, chat_id)
        connection = self.data["connection"] = await ConnectionsMiddleware.get_chat_from_db(chat_id, is_connected=True)

        doc = Doc(
            Bold(Template(_("Connected to chat {chat_name} successfully!"), chat_name=connection.title)),
            Template(_("Use {command} to disconnect"), command="/disconnect"),
        )

        await self.event.reply(str(doc))

        # List notes
        return await NotesList(self.event, **self.data)

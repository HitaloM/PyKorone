from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from stfu_tg import Bold, Doc, Template

from sophie_bot.filters.chat_status import ChatTypeFilter
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.middlewares.connections import ConnectionsMiddleware
from sophie_bot.modules.connections.utils.connection import set_connected_chat
from sophie_bot.modules.connections.utils.constants import CONNECTION_DISCONNECT_TEXT
from sophie_bot.modules.notes.callbacks import PrivateNotesStartUrlCallback
from sophie_bot.modules.notes.filters.pm_notes import PMNotesFilter
from sophie_bot.modules.notes.handlers.list import LIST_CMDS, NotesList
from sophie_bot.modules.notes.handlers.search import SEARCH_CMD
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _


@flags.help(exclude=True)
class PrivateNotesRedirectHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (~ChatTypeFilter("private"), CMDFilter((*LIST_CMDS, SEARCH_CMD)), PMNotesFilter())

    async def handle(self) -> Any:
        text = _("Please connect to the chat to interact with chat notes")
        buttons = InlineKeyboardBuilder()

        connection = self.connection
        buttons.add(
            InlineKeyboardButton(
                text=_("🔌 Connect"),
                url=PrivateNotesStartUrlCallback(chat_id=connection.tid).pack(),
            )
        )
        await self.event.reply(text, reply_markup=buttons.as_markup())


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
        if not (connection := await ConnectionsMiddleware.get_chat_from_db(chat_id, is_connected=True)):
            return await self.event.reply(
                _("Chat not found in the database. Please try to disconnect and connect again.")
            )

        self.data["connection"] = connection

        doc = Doc(
            Bold(Template(_("Connected to chat {chat_name} successfully!"), chat_name=connection.title)),
            Template(_("Use {command} to disconnect"), command="/disconnect"),
            _("⏳ This connection will last for 48 hours."),
        )

        markup = ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text=str(CONNECTION_DISCONNECT_TEXT))]], resize_keyboard=True
        )

        await self.event.reply(str(doc), reply_markup=markup)

        # List notes
        return await NotesList(self.event, **self.data)

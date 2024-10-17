from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.chat_status import ChatTypeFilter
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.notes.callbacks import PrivateNotesStartUrlCallback
from sophie_bot.modules.notes.filters.pm_notes import PMNotesFilter
from sophie_bot.modules.notes.handlers.list import LIST_CMDS
from sophie_bot.modules.notes.handlers.search import SEARCH_CMD
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _


@flags.help(exclude=True)
class PrivateNotesRedirectHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (
            ~ChatTypeFilter("private"),
            CMDFilter((*LIST_CMDS, SEARCH_CMD)),
            PMNotesFilter(),
            ~UserRestricting(admin=True),
        )

    async def handle(self) -> Any:
        text = _("Please connect to the chat to interact with chat notes")
        buttons = InlineKeyboardBuilder()

        connection = self.connection()
        buttons.add(
            InlineKeyboardButton(
                text=_("🔌 Connect"),
                url=PrivateNotesStartUrlCallback(chat_id=connection.id).pack(),
            )
        )
        await self.event.reply(text, reply_markup=buttons.as_markup())

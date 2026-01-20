from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from stfu_tg import Code, Italic, Template

from sophie_bot.db.models import NoteModel
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.notes.callbacks import DeleteAllNotesCallback
from sophie_bot.modules.logging.events import LogEvent
from sophie_bot.modules.logging.utils import log_event
from sophie_bot.utils.handlers import (
    SophieCallbackQueryHandler,
    SophieMessageHandler,
)
from sophie_bot.utils.exception import SophieException
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(description=l_("Deletes all notes."))
class DelAllNotesHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter(("clearall")), UserRestricting(admin=True)

    async def handle(self) -> Any:
        connection = self.connection

        if not self.event.from_user:
            raise SophieException("No user")

        buttons = InlineKeyboardBuilder()
        buttons.add(
            InlineKeyboardButton(
                text=_("🗑 Delete all"), callback_data=DeleteAllNotesCallback(user_id=self.event.from_user.id).pack()
            ),
        )
        buttons.add(
            InlineKeyboardButton(text=_("🚫 Cancel"), callback_data="cancel"),
        )

        await self.event.reply(
            str(
                Template(
                    _("Do you want to delete all the notes in the {chat_name}?"), chat_name=Italic(connection.title)
                ),
            ),
            reply_markup=buttons.as_markup(),
        )


class DelAllNotesCallbackHandler(SophieCallbackQueryHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return DeleteAllNotesCallback.filter(), UserRestricting(admin=True)

    async def handle(self) -> Any:
        connection = self.connection

        if not self.event.message:
            raise SophieException("No message")

        data: DeleteAllNotesCallback = self.data["callback_data"]
        user_id = self.event.from_user.id

        if user_id != data.user_id:
            return await self.event.answer(_("Only the initiator can confirm deleting all notes"))

        deleted = await NoteModel.delete_all_notes(connection.tid)
        await log_event(connection.tid, user_id, LogEvent.ALL_NOTES_DELETED)

        text = Template(
            _("🗑 All the notes ({removed_count}) have been deleted in the {chat_name}"),
            removed_count=Code(deleted.deleted_count if deleted else 0),
            chat_name=connection.title,
        )

        await self.event.message.edit_text(str(text))  # type: ignore

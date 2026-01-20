from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from ass_tg.types import WordArg
from stfu_tg import Italic, KeyValue, Section

from sophie_bot.db.models import NoteModel
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.middlewares.connections import ChatConnection
from sophie_bot.modules.logging.events import LogEvent
from sophie_bot.modules.logging.utils import log_event
from sophie_bot.modules.notes.utils.names import format_notes_aliases
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.args(notename=WordArg(l_("Note name")))
@flags.help(description=l_("Deletes notes."))
class DelNote(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter(("delnote", "clear")), UserRestricting(admin=True)

    async def handle(self) -> Any:
        if not self.event.from_user:
            return

        chat: ChatConnection = self.data["connection"]

        raw_name = self.data["notename"]
        note = await NoteModel.get_by_notenames(chat.tid, (raw_name,))

        if not note:
            return await self.event.reply(_("No notes was found with {name} name.").format(name=Italic(raw_name)))

        await note.delete()
        await log_event(chat.tid, self.event.from_user.id, LogEvent.NOTE_DELETED, {"note_names": note.names})

        await self.event.reply(
            str(
                Section(
                    KeyValue(_("Chat"), chat.title),
                    KeyValue((_("Name") if len(note.names) == 1 else _("Names")), format_notes_aliases(note.names)),
                    title=_("Note was successfully deleted"),
                )
            )
        )

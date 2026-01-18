from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from ass_tg.types import TextArg
from stfu_tg import Code, Doc, Italic, KeyValue, Section, Template

from sophie_bot.db.models import NoteModel
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.notes.utils.list import format_notes_list
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_

SEARCH_CMD = "search"


@flags.args(text=TextArg(l_("Text to search")))
@flags.disableable(name="notes")
@flags.help(description=l_("Searches for note contents"))
class NotesSearchHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter(SEARCH_CMD),)

    async def handle(self) -> Any:
        connection = self.connection

        to_search: str = self.data["text"]
        notes = await NoteModel.search_chat_notes(connection.tid, to_search)

        if not notes:
            return await self.event.reply(
                str(Template(_("No notes found by the provided search pattern {pattern}."), pattern=Code(to_search)))
            )

        doc = Doc(
            Section(
                KeyValue(_("Search pattern"), Italic(to_search)),
                format_notes_list(notes),
                title=_("Notes in {chat_name}").format(chat_name=connection.title),
            ),
            " ",
            Template(
                _("Use {cmd} to retrieve a note. Example: {cmd_example}"),
                cmd=Italic(_("#(Note name)")),
                cmd_example=Code(f"#{notes[0].names[0]}"),
            ),
        )

        return await self.event.reply(str(doc))

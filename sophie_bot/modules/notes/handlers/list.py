from typing import Any, Optional

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from ass_tg.types import OptionalArg, TextArg
from stfu_tg import Code, Doc, Italic, KeyValue, Section, Template

from sophie_bot.db.models.notes import NoteModel
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.notes.utils.list import format_notes_list
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_

LIST_CMDS = ("notes", "saved", "notelist")


@flags.args(search=OptionalArg(TextArg(l_("?Search notes"))))
@flags.help(description=l_("Lists available notes."))
@flags.disableable(name="notes")
class NotesList(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter(LIST_CMDS),)

    async def handle(self) -> Any:
        to_search: Optional[str] = self.data.get("search")
        connection = self.connection

        notes = await NoteModel.get_chat_notes(connection.tid)
        if to_search:
            notes = [note for note in notes if any(to_search in name for name in note.names)]

        if to_search and not notes:
            return await self.event.reply(
                str(
                    Template(
                        _("No notes found by the provided search pattern {pattern} in {chat_name}."),
                        pattern=Italic(to_search),
                        chat_name=Italic(connection.title),
                    )
                )
            )
        elif not notes:
            return await self.event.reply(
                str(Template(_("No notes found in {chat_name}."), chat_name=Italic(connection.title)))
            )

        doc = Doc(
            Section(
                KeyValue(_("Search pattern"), Italic(to_search)) if to_search else None,
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

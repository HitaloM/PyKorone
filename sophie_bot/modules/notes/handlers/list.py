from typing import Any, List, Optional

from aiogram import flags
from aiogram.handlers import MessageHandler
from ass_tg.types import OptionalArg, TextArg
from stfu_tg import Code, Doc, Italic, KeyValue, Section, Template, VList

from sophie_bot.db.models.notes import NoteModel
from sophie_bot.middlewares.connections import ChatConnection
from sophie_bot.modules.legacy_modules.utils.disable import disableable_dec
from sophie_bot.modules.notes.utils.names import format_notes_aliases
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.args(search=OptionalArg(TextArg(l_("Search notes"))))
@flags.help(description=l_("Lists available notes."))
@disableable_dec("notes")
class NotesList(MessageHandler):
    @staticmethod
    async def note_names(
        notes: List[NoteModel], note_group: Optional[str], to_search: Optional[str]
    ) -> tuple[tuple[str, ...], ...]:
        return tuple(
            note.names
            for note in notes
            if not to_search or any(to_search in name for name in note.names) and note.note_group == note_group
        )

    @staticmethod
    async def note_groups(notes: List[NoteModel]) -> set[str | None]:
        return {note.note_group for note in notes}

    @staticmethod
    def format_notes_list(notes: List[NoteModel]) -> VList:
        formatted_notes = [
            (
                Section(
                    Italic(note.description),
                    title=format_notes_aliases(note.names),
                    title_bold=False,
                    title_underline=False,
                    title_postfix="",
                    indent=3,
                )
                if note.description
                else format_notes_aliases(note.names)
            )
            for note in notes
        ]

        return VList(*formatted_notes)

    def format_notes_list_group(self, notes: List[NoteModel], note_group: Optional[str]) -> Section:
        group_notes = list(filter(lambda note: note.note_group == note_group, notes))

        return Section(
            self.format_notes_list(group_notes), title=f"${(note_group or 'default').upper()}", title_bold=True
        )

    def format_notes_list_optional_groups(self, notes: List[NoteModel]) -> tuple[VList | Section, ...]:
        groups = {note.note_group for note in notes}

        if groups == {None} or True:
            return (self.format_notes_list(notes),)

        return tuple(self.format_notes_list_group(notes, group) for group in groups)

    async def handle(self) -> Any:
        to_search: Optional[str] = self.data["search"]
        connection: ChatConnection = self.data["connection"]

        notes = await NoteModel.get_chat_notes(connection.id)
        if to_search:
            notes = [note for note in notes if any(to_search in name for name in note.names)]

        if to_search and not notes:
            return await self.event.reply(
                _("No notes found by the provided search pattern {pattern}.").format(pattern=Italic(to_search))
            )
        elif not notes:
            return await self.event.reply(_("No notes found."))

        doc = Doc(
            Section(
                KeyValue(_("Search pattern"), Italic(to_search)) if to_search else None,
                *self.format_notes_list_optional_groups(notes),
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

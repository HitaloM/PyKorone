from typing import Any, List, Optional

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.types import InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from ass_tg.types import OptionalArg, TextArg
from sophie_bot.filters.admin_rights import UserRestricting
from stfu_tg import Code, Doc, Italic, KeyValue, Section, Template, VList

from sophie_bot.db.models.notes import NoteModel
from sophie_bot.filters.chat_status import ChatTypeFilter
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.middlewares.connections import ChatConnection
from sophie_bot.modules.notes.callbacks import PrivateNotesStartUrlCallback
from sophie_bot.modules.notes.filters.pm_notes import PMNotesFilter
from sophie_bot.modules.notes.utils.names import format_notes_aliases
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_

LIST_CMD_FILTER = CMDFilter(("notes", "saved", "notelist"))


class PrivateNotesRedirectHandler(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return ~ChatTypeFilter("private"), LIST_CMD_FILTER, PMNotesFilter(), ~UserRestricting(admin=True)

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


@flags.args(search=OptionalArg(TextArg(l_("Search notes"))))
@flags.help(description=l_("Lists available notes."))
@flags.disableable(name="notes")
class NotesList(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (LIST_CMD_FILTER,)

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

    def format_notes_list_group(self, notes: List[NoteModel], note_group: str) -> Section:
        group_notes = list(filter(lambda note: note.note_group == note_group, notes))

        return Section(self.format_notes_list(group_notes), title=f"${note_group.upper()}", title_bold=True)

    def format_notes_list_optional_groups(self, notes: List[NoteModel]) -> list[VList | Section]:
        groups = {note.note_group for note in notes}

        content = []
        for group in groups:
            if not group:
                content.append(self.format_notes_list(list(note for note in notes if not note.note_group)))
            else:
                content.append(self.format_notes_list_group(notes, group))

        return content

    async def handle(self) -> Any:
        to_search: Optional[str] = self.data.get("search")
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

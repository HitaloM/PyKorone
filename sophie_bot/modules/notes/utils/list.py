from stfu_tg import Italic, Section, VList

from sophie_bot.db.models import NoteModel
from sophie_bot.modules.notes.utils.names import format_notes_aliases


def format_notes_list(notes: list[NoteModel]) -> VList:
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

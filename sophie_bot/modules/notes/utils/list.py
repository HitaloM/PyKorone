from stfu_tg import HList, Italic, Section, Spacer, VList

from sophie_bot.constants import AI_EMOJI
from sophie_bot.db.models import NoteModel
from sophie_bot.modules.notes.utils.names import format_notes_aliases


def format_notes_list(notes: list[NoteModel]) -> VList:
    formatted_notes = [
        (
            Section(
                HList(AI_EMOJI + Spacer() if note.ai_description else None, Italic(note.description)),
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

from aiogram import Router

from sophie_bot.utils.i18n import lazy_gettext as l_

from .handlers.delete import DelNote
from .handlers.delete_all import DelAllNotesCallbackHandler, DelAllNotesHandler
from .handlers.get import GetNote, HashtagGetNote
from .handlers.legacy_button import LegacyStartNoteButton
from .handlers.list import NotesList
from .handlers.pmnotes_handler import (
    PrivateNotesConnectHandler,
    PrivateNotesRedirectHandler,
)
from .handlers.pmnotes_setting import PMNotesControl, PMNotesStatus
from .handlers.save import SaveNote
from .handlers.search import NotesSearchHandler
from .magic_handlers.export import export
from .magic_handlers.filter import get_filter
from .utils.legacy_buttons import BUTTONS

router = Router(name="notes")


__module_name__ = l_("Notes")
__module_emoji__ = "📗"

__filters__ = get_filter()
__export__ = export


BUTTONS.update({"note": "btnnotesm", "#": "btnnotesm"})


def __pre_setup__():
    # PM notes
    router.message.register(PMNotesControl, *PMNotesControl.filters())
    router.message.register(PMNotesStatus, *PMNotesStatus.filters())

    router.message.register(PrivateNotesConnectHandler, *PrivateNotesConnectHandler.filters())
    router.message.register(PrivateNotesRedirectHandler, *PrivateNotesRedirectHandler.filters())

    router.message.register(NotesList, *NotesList.filters())
    router.message.register(GetNote, *GetNote.filters())
    router.message.register(HashtagGetNote, *HashtagGetNote.filters())
    router.message.register(NotesSearchHandler, *NotesSearchHandler.filters())

    router.message.register(DelNote, *DelNote.filters())
    router.message.register(SaveNote, *SaveNote.filters())

    router.message.register(DelAllNotesHandler, *DelAllNotesHandler.filters())
    router.callback_query.register(DelAllNotesCallbackHandler, *DelAllNotesCallbackHandler.filters())

    # Legacy note buttons
    router.message.register(LegacyStartNoteButton, *LegacyStartNoteButton.filters())

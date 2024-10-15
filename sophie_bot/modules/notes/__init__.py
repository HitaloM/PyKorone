from aiogram import Router

from sophie_bot.utils.i18n import lazy_gettext as l_

from ...filters.admin_rights import UserRestricting
from ...filters.cmd import CMDFilter
from .handlers.get import GetNote, HashtagGetNote
from .handlers.list import NotesList, PrivateNotesRedirectHandler
from .handlers.privatenotes import PrivateNotesConnectHandler
from .handlers.save import SaveNote

router = Router(name="notes")


__module_name__ = l_("Notes")
__module_emoji__ = "🗒"


def __pre_setup__():

    router.message.register(PrivateNotesConnectHandler, *PrivateNotesConnectHandler.filters())
    router.message.register(PrivateNotesRedirectHandler, *PrivateNotesRedirectHandler.filters())

    router.message.register(NotesList, *NotesList.filters())
    router.message.register(GetNote, *GetNote.filters())
    router.message.register(HashtagGetNote, *HashtagGetNote.filters())

    # router.message.register(DelNote, CMDFilter(("delnote", "clear")), UserRestricting(admin=True))
    router.message.register(SaveNote, CMDFilter(("save", "addnote", "savenote")), UserRestricting(admin=True))

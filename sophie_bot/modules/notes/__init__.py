from aiogram import Router

from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.utils.i18n import lazy_gettext as l_

from ...filters.admin_rights import UserRestricting
from .handlers.delete import DelNote
from .handlers.get import GetNote
from .handlers.list import NotesList
from .handlers.save import SaveNote

router = Router(name="notes")


__module_name__ = l_("Users")
__module_emoji__ = "🗒"


def __pre_setup__():
    router.message.register(NotesList, CMDFilter(("notes", "saved", "notelist")))
    router.message.register(GetNote, CMDFilter("get"))

    router.message.register(DelNote, CMDFilter(("delnote", "clear")), UserRestricting(admin=True))
    router.message.register(SaveNote, CMDFilter(("save", "addnote", "savenote")), UserRestricting(admin=True))

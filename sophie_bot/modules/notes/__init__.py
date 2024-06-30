from aiogram import Router

from sophie_bot.filters.cmd import CMDFilter

from ...filters.admin_rights import UserRestricting
from .handlers.delete import DelNote
from .handlers.get import GetNote
from .handlers.list import NotesList
from .handlers.save import SaveNote

router = Router(name="notes")


def __pre_setup__():
    router.message.register(NotesList, CMDFilter(("notes", "saved", "notelist")))
    router.message.register(GetNote, CMDFilter("get"))

    router.message.register(DelNote, CMDFilter(("delnote", "clear")), UserRestricting(admin=True))
    router.message.register(SaveNote, CMDFilter(("save", "addnote", "savenote")), UserRestricting(admin=True))

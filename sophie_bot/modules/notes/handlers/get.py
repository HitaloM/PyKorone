from typing import Any

from aiogram import F, flags
from aiogram.dispatcher.event.handler import CallbackType
from ass_tg.types import OneOf, OptionalArg, WordArg
from stfu_tg import Bold, HList, Italic, Title

from sophie_bot.db.models import NoteModel
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.middlewares.connections import ChatConnection
from sophie_bot.modules.notes.utils.send import send_saveable
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.args(notename=WordArg(l_("Note name")), raw=OptionalArg(OneOf("noformat", "raw")))
@flags.help(description=l_("Retrieve the note."))
class GetNote(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter("get"),)

    async def handle(self) -> Any:
        chat: ChatConnection = self.data["connection"]

        note_name = self.data["notename"]
        note = await NoteModel.get_by_notenames(chat.id, (note_name,))

        if not note and self.data.get("get_error_on_404", True):
            return await self.event.reply(_("No note was found with {name} name.").format(name=Italic(note_name)))
        elif not note:
            return

        title = Bold(HList(Title(f"📗 #{note_name}", bold=False), note.description or ""))
        legacy_title = HList(Title(f"📙 #{note_name}", bold=False), note.description or "")

        raw = bool(self.data.get("raw", False))
        await send_saveable(self.event, self.event.chat.id, note, title=title, legacy_title=str(legacy_title), raw=raw)


class HashtagGetNote(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (F.text.regexp(r"^#([\w-]+)"),)

    async def handle(self) -> Any:
        self.data["get_error_on_404"] = False
        self.data["notename"] = (self.event.text or "").removeprefix("#")
        return await GetNote(self.event, **self.data)

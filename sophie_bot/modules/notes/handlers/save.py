from typing import Any, Optional, Sequence

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from ass_tg.types import DividedArg, OptionalArg, SurroundedArg, TextArg, WordArg
from bson import Code
from stfu_tg import KeyValue, Section, Template

from sophie_bot.db.models import NoteModel
from sophie_bot.db.models.notes import Saveable
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.middlewares.connections import ChatConnection
from sophie_bot.modules.notes.utils.names import format_notes_aliases
from sophie_bot.modules.notes.utils.parse import parse_saveable
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.args(
    notenames=DividedArg(WordArg(l_("Note names"))),
    # note_group=OptionalArg(StartsWithArg("$", WordArg(l_("Group")))),
    description=OptionalArg(SurroundedArg(TextArg(l_("?Description")))),
    raw_text=OptionalArg(TextArg(l_("Content"), parse_entities=True)),
)
@flags.help(description=l_("Save the note."))
class SaveNote(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter(("save", "addnote")), UserRestricting(admin=True)

    async def handle(self) -> Any:
        connection: ChatConnection = self.data["connection"]
        raw_text: Optional[str] = self.data.get("raw_text")

        notenames: tuple[str, ...] = tuple(name.lower() for name in self.data["notenames"])

        text_offset = self.data["arg"].value["raw_text"].offset

        saveable = await parse_saveable(self.event, raw_text, offset=text_offset)
        is_created = await self.save(saveable, notenames, connection.tid, self.data)

        await self.event.reply(
            str(
                Section(
                    KeyValue("Note names", format_notes_aliases(notenames)),
                    # KeyValue("Group", self.data.get("note_group", "-")),
                    KeyValue("Description", self.data.get("description", "-")),
                    title=_("Note was successfully created") if is_created else _("Note was successfully updated"),
                )
                + Template(
                    _("Use {cmd} to retrieve this note."),
                    cmd=Code(f"#{self.data['notenames'][0]}"),
                )
            )
        )

    async def save(self, saveable: Saveable, notenames: Sequence[str], chat_id: int, data: dict) -> bool:
        model = await NoteModel.get_by_notenames(chat_id, notenames)

        saveable_data = {
            "chat_id": chat_id,
            "names": notenames,
            "note_group": data.get("note_group"),
            "description": data.get("description"),
            "ai_description": False,
            **saveable.model_dump(),
        }

        if not model:
            model = NoteModel(**saveable_data)
            await model.create()
            return True

        await model.set(saveable_data)
        return False

from typing import Any, Sequence

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from ass_tg.types import DividedArg, OptionalArg, SurroundedArg, TextArg, WordArg
from bson import Code
from stfu_tg import KeyValue, Section, Template

from ass_tg.types.base_abc import ParsedArg
from sophie_bot.db.models import NoteModel
from sophie_bot.db.models.notes import Saveable
from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.middlewares.connections import ChatConnection
from sophie_bot.modules.notes.utils.buttons_processor.ass_types.TextWithButtonsArg import TextWithButtonsArg
from sophie_bot.modules.notes.utils.buttons_processor.buttons import ButtonsList
from sophie_bot.modules.notes.utils.names import format_notes_aliases
from sophie_bot.modules.notes.utils.parse import parse_saveable
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.args(
    notenames=DividedArg(WordArg(l_("Note names"))),
    # note_group=OptionalArg(StartsWithArg("$", WordArg(l_("Group")))),
    description=OptionalArg(SurroundedArg(TextArg(l_("?Description")))),
    text_with_buttons=TextWithButtonsArg(),
)
@flags.help(description=l_("Save the note."))
class SaveNote(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter(("save", "addnote")), UserRestricting(admin=True)

    async def handle(self) -> Any:
        connection: ChatConnection = self.data["connection"]

        text_with_buttons: dict[str, Any] = self.data["text_with_buttons"]
        raw_text_parsed: ParsedArg[str] = text_with_buttons.get("text")
        raw_text = raw_text_parsed.value
        text_offset = raw_text_parsed.offset

        raw_buttons: ButtonsList = text_with_buttons.get("buttons").value
        buttons = ButtonsList.from_ass(raw_buttons)

        notenames: tuple[str, ...] = tuple(name.lower() for name in self.data["notenames"])

        saveable = await parse_saveable(self.event, raw_text, offset=text_offset, buttons=buttons)
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

        # Explicitly type the saveable data to ensure type safety
        saveable_dump = saveable.model_dump()
        saveable_data: dict[str, Any] = {
            "chat_id": chat_id,
            "names": notenames,
            "note_group": data.get("note_group"),
            "description": data.get("description"),
            "ai_description": False,
            "text": saveable_dump["text"],
            "file": saveable_dump["file"],
            "buttons": saveable_dump["buttons"],
            "parse_mode": saveable_dump["parse_mode"],
            "preview": saveable_dump["preview"],
            "version": saveable_dump["version"],
        }

        if not model:
            model = NoteModel(**saveable_data)
            await model.create()
            return True

        await model.set(saveable_data)
        return False

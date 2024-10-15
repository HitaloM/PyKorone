from typing import Any, Tuple

from aiogram import flags
from aiogram.handlers import MessageHandler
from aiogram.types import Message
from ass_tg.types import DividedArg, OptionalArg, SurroundedArg, TextArg, WordArg
from bson import Code
from stfu_tg import KeyValue, Section, Template

from sophie_bot.db.models import NoteModel
from sophie_bot.db.models.notes import Saveable
from sophie_bot.middlewares.connections import ChatConnection
from sophie_bot.modules.notes.utils.legacy_notes import get_parsed_note_list
from sophie_bot.modules.notes.utils.parse import parse_saveable
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.args(
    notenames=DividedArg(WordArg(l_("Note names"))),
    # note_group=OptionalArg(StartsWithArg("$", WordArg(l_("Group")))),
    description=OptionalArg(SurroundedArg(TextArg(l_("Description")))),
    raw_text=OptionalArg(TextArg(l_("Text"), parse_entities=True)),
)
@flags.help(description=l_("Save the note."))
class SaveNote(MessageHandler):
    async def handle(self) -> Any:
        return await self.handle_save()

    async def handle_save(self) -> Any:
        connection: ChatConnection = self.data["connection"]

        created, is_legacy = await self.save(self.event, connection.id, self.data)

        await self.event.reply(
            str(
                Section(
                    _("Legacy mode") if is_legacy else None,
                    KeyValue("Note names", ", ".join(self.data["notenames"])),
                    # KeyValue("Group", self.data.get("note_group", "-")),
                    KeyValue("Description", self.data.get("description", "-")),
                    title=_("Note was successfully created") if created else _("Note was successfully updated"),
                )
                + Template(
                    _("Use {cmd} to retrieve this note."),
                    cmd=Code(f"#{self.data['notenames'][0]}"),
                )
            )
        )

    async def parse_legacy(self) -> Saveable:
        note = await get_parsed_note_list(self.event)

        return Saveable(
            text=note.get("text", ""),
            file=note.get("file"),
            # buttons=note.get("buttons"),
            parse_mode=note["parse_mode"],
            preview=note.get("preview", False),
        )

    async def save(self, message: Message, chat_id: int, data: dict) -> Tuple[bool, bool]:
        model = await NoteModel.get_by_notenames(chat_id, data["notenames"])

        # Legacy
        if message.reply_to_message:
            note_data = await self.parse_legacy()
            legacy_parse = True
        else:
            note_data = await parse_saveable(message, data.get("raw_text"))
            legacy_parse = False

        data = {
            "chat_id": chat_id,
            "names": data["notenames"],
            "note_group": data.get("note_group"),
            "description": data.get("description"),
            **note_data.model_dump(),
        }

        if not model:
            model = NoteModel(**data)
            await model.create()
            return True, legacy_parse

        await model.set(data)
        return False, legacy_parse

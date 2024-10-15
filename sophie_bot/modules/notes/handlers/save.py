from typing import Any

from aiogram import flags
from aiogram.handlers import MessageHandler
from aiogram.types import Message
from ass_tg.types import (
    DividedArg,
    OptionalArg,
    StartsWithArg,
    SurroundedArg,
    TextArg,
    WordArg,
)
from bson import Code
from stfu_tg import KeyValue, Section, Template

from sophie_bot.db.models import NoteModel
from sophie_bot.db.models.notes import Saveable
from sophie_bot.middlewares.connections import ChatConnection
from sophie_bot.modules.notes.utils.parse import parse_saveable
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.args(
    notenames=DividedArg(WordArg(l_("Note names"))),
    note_group=OptionalArg(StartsWithArg("$", WordArg(l_("Group")))),
    description=OptionalArg(SurroundedArg(TextArg(l_("Description")))),
    raw_text=OptionalArg(TextArg(l_("Text"), parse_entities=True)),
)
@flags.help(description=l_("Save the note."))
class SaveNote(MessageHandler):
    async def handle(self) -> Any:
        return await self.handle_save()

    async def handle_save(self) -> Any:
        connection: ChatConnection = self.data["connection"]

        created = await self.save(self.event, connection.id, self.data)

        await self.event.reply(
            str(
                Section(
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

    @staticmethod
    async def save(message: Message, chat_id: int, data: dict) -> bool:
        model = await NoteModel.get_by_notenames(chat_id, data["notenames"])

        note_data: Saveable = await parse_saveable(message, data.get("raw_text"))

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
            return True

        await model.set(data)
        return False

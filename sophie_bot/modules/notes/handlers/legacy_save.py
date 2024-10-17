from datetime import datetime
from typing import Any

from aiogram import flags
from aiogram.dispatcher.event.handler import CallbackType
from ass_tg.types import WordArg

from sophie_bot.filters.admin_rights import UserRestricting
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.modules.notes.utils.legacy_notes import get_parsed_note_list
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.services.db import db
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.help(exclude=True)
@flags.args(notename=WordArg(l_("Note name")))
class LegacySaveNote(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return CMDFilter("legacysave"), UserRestricting(admin=True)

    async def handle(self) -> Any:
        message = self.event
        connection = self.connection()

        notename: str = self.data["notename"].lower()

        sym = None
        if any((sym := s) in notename for s in ("#", "&")):
            await message.reply("Notename cannot contain - " + sym)
            return

        note_names = notename.split("|")

        note = await get_parsed_note_list(message)

        note["names"] = note_names
        chat_id = connection.id
        note["chat_id"] = chat_id

        if "text" not in note and "file" not in note:
            await message.reply("Is blank note text or file. Please provide content.")
            return

        if old_note := await db.notes.find_one({"chat_id": chat_id, "names": {"$in": note_names}}):
            text = "Note updated in {chat_title}!\n"
            if "created_date" in old_note:
                note["created_date"] = old_note["created_date"]
                note["created_user"] = old_note["created_user"]
            note["edited_date"] = datetime.now()
            note["edited_user"] = message.from_user.id
        else:
            text = "Note saved in {chat_title}!\n"
            note["created_date"] = datetime.now()
            note["created_user"] = message.from_user.id

        await db.notes.replace_one({"_id": old_note["_id"]} if old_note else note, note, upsert=True)

        text += "You can get note using #{note_name}"
        text = text.format(note_name=note_names[0], chat_title=connection.title)

        await message.reply(text)

from re import search
from typing import Any

from aiogram import F
from aiogram.dispatcher.event.handler import CallbackType
from aiogram.filters import CommandStart
from stfu_tg import Bold, HList, Title

from sophie_bot.db.models import NoteModel
from sophie_bot.modules.notes.utils.send import send_saveable
from sophie_bot.utils.handlers import SophieMessageHandler
from sophie_bot.utils.exception import SophieException


class LegacyStartNoteButton(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CommandStart(deep_link=True, magic=F.args.regexp(r"btnnotesm")),)

    async def handle(self) -> Any:
        message = self.event

        regex = search(r"btnnotesm_(.*)_(.*)", message.text)

        if not regex:
            return

        chat_id = int(regex.group(2))
        user_id = message.from_user.id
        note_name = regex.group(1)

        note = await NoteModel.get_by_notenames(chat_id, (note_name,))

        if not note:
            raise SophieException("No such note")

        title = Bold(HList(Title(f"📗 #{note_name}", bold=False), note.description or ""))

        await send_saveable(
            message,
            user_id,
            note,
            title=title,
            reply_to=message.message_id,
            connection=self.connection,
        )

from typing import Any

from aiogram import flags
from aiogram.handlers import MessageHandler
from ass_tg.types import WordArg
from stfu_tg import Italic, Title

from sophie_bot.db.models import NoteModel
from sophie_bot.middlewares.connections import ChatConnection
from sophie_bot.modules.notes.utils.send import send_saveable
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.args(notename=WordArg(l_("Note name")))
@flags.help(description=l_("Retrieve the note."))
class GetNote(MessageHandler):
    async def handle(self) -> Any:
        chat: ChatConnection = self.data["connection"]

        note_name = self.data["notename"]
        note = await NoteModel.get_by_notenames(chat.id, (note_name,))

        if not note:
            return await self.event.reply(_("No note was found with {name} name.").format(name=Italic(note)))

        title_text = f"🗒 #{note_name}"

        if note.description:
            title_text += f"- {note.description}"

        await send_saveable(self.event, self.chat.id, note, title=Title(title_text))

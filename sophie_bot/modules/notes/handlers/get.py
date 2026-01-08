import re
from typing import Any, Optional

from aiogram import F, flags
from aiogram.dispatcher.event.handler import CallbackType
from ass_tg.types import OneOf, OptionalArg, WordArg
from stfu_tg import Bold, HList, Italic, Title
from stfu_tg.doc import Element

from sophie_bot.db.models import NoteModel
from sophie_bot.filters.cmd import CMDFilter
from sophie_bot.middlewares.connections import ChatConnection
from sophie_bot.modules.notes.utils.combine import combine_saveables
from sophie_bot.modules.notes.utils.send import send_saveable
from sophie_bot.modules.utils_.base_handler import SophieMessageHandler
from sophie_bot.utils.i18n import gettext as _
from sophie_bot.utils.i18n import lazy_gettext as l_


@flags.args(notename=WordArg(l_("Note name")), raw=OptionalArg(OneOf("noformat", "?raw")))
@flags.help(description=l_("Retrieve the note."))
class GetNote(SophieMessageHandler):
    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (CMDFilter("get"),)

    async def handle(self) -> Any:
        chat: ChatConnection = self.data["connection"]

        note_name: str = self.data["notename"].removeprefix("#")
        note = await NoteModel.get_by_notenames(chat.tid, (note_name,))

        if not note and self.data.get("get_error_on_404", True):
            return await self.event.reply(_("No note was found with {name} name.").format(name=Italic(note_name)))
        elif not note:
            return

        title = Bold(HList(Title(f"📗 #{note_name}", bold=False), note.description or ""))

        raw = bool(self.data.get("raw", False))

        # Reply
        # TODO: Handle chat topics!
        if self.event.reply_to_message:
            reply_to = self.event.reply_to_message.message_id
        else:
            reply_to = self.event.message_id

        message = await send_saveable(
            self.event,
            self.event.chat.id,
            note,
            title=title,
            raw=raw,
            reply_to=reply_to,
            connection=chat,
        )

        return message


class HashtagGetNote(SophieMessageHandler):
    hashtag_regex = re.compile(r"#([\w-]+)")

    @staticmethod
    def filters() -> tuple[CallbackType, ...]:
        return (F.text.regexp(r".*#([\w-]+).*"),)

    async def _fine_note(self, note_name: str) -> Optional[NoteModel]:
        chat: ChatConnection = self.data["connection"]
        return await NoteModel.get_by_notenames(chat.tid, (note_name,))

    @staticmethod
    def _get_note_title(note_model: NoteModel) -> Element:
        return Bold(HList(Title(f"📗 #{note_model.names[0]}", bold=False), note_model.description or ""))

    async def handle(self) -> Any:
        raw_text = self.event.text or ""

        matches = self.hashtag_regex.findall(raw_text)

        # Remove duplicates
        matches = list(set(matches))

        notes_to_stack = [note for match in matches if (note := await self._fine_note(match))]

        if not notes_to_stack:
            return

        # Limit to 3 first items
        if len(notes_to_stack) > 3:
            notes_to_stack = notes_to_stack[:3]

        saveable = combine_saveables(*((item, self._get_note_title(item)) for item in notes_to_stack))

        # Reply
        # TODO: Handle chat topics!
        if self.event.reply_to_message:
            reply_to = self.event.reply_to_message.message_id
        else:
            reply_to = self.event.message_id

        chat: ChatConnection = self.data["connection"]
        return await send_saveable(self.event, self.event.chat.id, saveable, reply_to=reply_to, connection=chat)

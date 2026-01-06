from typing import Sequence

from pydantic import TypeAdapter
from pydantic_ai import RunContext
from typing_extensions import TypedDict

from sophie_bot.db.models import NoteModel
from sophie_bot.modules.ai.utils.ai_chatbot_reply import SophieAIToolContenxt


class AIChatNote(TypedDict):
    names: Sequence[str]
    text: str | None


notes_ta = TypeAdapter(list[AIChatNote])


class AIChatNotesFunc:
    @staticmethod
    def from_model(note: NoteModel):
        return AIChatNote(names=note.names, text=note.text)

    async def __call__(self, ctx: RunContext["SophieAIToolContenxt"]) -> list["AIChatNote"]:
        notes = await NoteModel.get_chat_notes(ctx.deps.connection.tid)
        return notes_ta.validate_python(note.model_dump() for note in notes)

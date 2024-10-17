from sophie_bot.db.models import NoteModel


async def export(chat_id):
    data = []
    notes = await NoteModel.get_chat_notes(chat_id)
    for note in notes:
        data.append(note.model_dump(mode="json"))

    return {"notes": data}

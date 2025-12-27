from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.notes import NoteModel
from sophie_bot.utils.api.auth import get_current_user
from .schemas import NoteResponse, NoteUpdate
from .utils import get_chat_and_verify_admin

router = APIRouter()


@router.patch("/{chat_id}/{note_name}", response_model=NoteResponse)
async def update_note(
    chat_id: int,
    note_name: str,
    note_data: NoteUpdate,
    user: Annotated[ChatModel, Depends(get_current_user)],
) -> NoteResponse:
    await get_chat_and_verify_admin(chat_id, user)

    note = await NoteModel.get_by_notenames(chat_id, [note_name])
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    update_dict = note_data.model_dump(exclude_unset=True)

    if "names" in update_dict:
        if not update_dict["names"]:
            raise HTTPException(status_code=400, detail="Note names cannot be empty")

        # Check if new names are taken by other notes
        existing = await NoteModel.get_by_notenames(chat_id, update_dict["names"])
        if existing and existing.id != note.id:
            raise HTTPException(status_code=400, detail=f"One of the names is already taken: {existing.names}")

    for key, value in update_dict.items():
        setattr(note, key, value)

    note.edited_date = datetime.now(timezone.utc)
    note.edited_user = user.chat_id
    await note.save()

    return NoteResponse(
        names=note.names,
        text=note.text,
        file=note.file,
        buttons=note.buttons,
        parse_mode=note.parse_mode,
        preview=note.preview,
        description=note.description,
        ai_description=note.ai_description,
        note_group=note.note_group,
        created_date=note.created_date,
        edited_date=note.edited_date,
    )

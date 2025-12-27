from __future__ import annotations

from datetime import datetime, timezone
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.notes import NoteModel
from sophie_bot.utils.api.auth import get_current_user
from .schemas import NoteCreate, NoteResponse
from .utils import get_chat_and_verify_admin

router = APIRouter()


@router.post("/{chat_id}", response_model=NoteResponse, status_code=status.HTTP_201_CREATED)
async def create_note(
    chat_id: int,
    note_data: NoteCreate,
    user: Annotated[ChatModel, Depends(get_current_user)],
) -> NoteResponse:
    chat = await get_chat_and_verify_admin(chat_id, user)

    if not note_data.names:
        raise HTTPException(status_code=400, detail="Note names cannot be empty")

    # Check if any of the names are already taken
    existing = await NoteModel.get_by_notenames(chat_id, note_data.names)
    if existing:
        raise HTTPException(status_code=400, detail=f"One of the names is already taken: {existing.names}")

    note = NoteModel(
        chat_id=chat_id,
        chat=chat.id,  # type: ignore[arg-type]
        names=note_data.names,
        text=note_data.text,
        file=note_data.file,
        buttons=note_data.buttons,
        parse_mode=note_data.parse_mode,
        preview=note_data.preview,
        description=note_data.description,
        ai_description=note_data.ai_description,
        note_group=note_data.note_group,
        created_date=datetime.now(timezone.utc),
        created_user=user.chat_id,
    )
    await note.insert()

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

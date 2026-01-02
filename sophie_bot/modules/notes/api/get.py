from __future__ import annotations

from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException

from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.notes import NoteModel
from sophie_bot.utils.api.auth import get_current_user
from .schemas import NoteResponse
from .utils import get_chat_and_verify_admin

router = APIRouter()


@router.get("/{chat_id}", response_model=list[NoteResponse])
async def list_notes(
    chat_id: int,
    user: Annotated[ChatModel, Depends(get_current_user)],
) -> list[NoteResponse]:
    await get_chat_and_verify_admin(chat_id, user)

    notes = await NoteModel.get_chat_notes(chat_id)
    return [
        NoteResponse(
            id=n.id,  # type: ignore[arg-type]
            names=n.names,
            text=n.text,
            file=n.file,
            buttons=n.buttons,
            parse_mode=n.parse_mode,
            preview=n.preview,
            description=n.description,
            ai_description=n.ai_description,
            note_group=n.note_group,
            created_date=n.created_date,
            edited_date=n.edited_date,
        )
        for n in notes
    ]


@router.get("/{chat_id}/{note_id}", response_model=NoteResponse)
async def get_note(
    chat_id: int,
    note_id: PydanticObjectId,
    user: Annotated[ChatModel, Depends(get_current_user)],
) -> NoteResponse:
    await get_chat_and_verify_admin(chat_id, user)

    note = await NoteModel.get(note_id)
    if not note or note.chat_id != chat_id:
        raise HTTPException(status_code=404, detail="Note not found")

    return NoteResponse(
        id=note.id,  # type: ignore[arg-type]
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

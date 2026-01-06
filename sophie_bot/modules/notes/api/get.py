from __future__ import annotations

from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException

from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.notes import NoteModel
from sophie_bot.utils.api.auth import get_current_user
from .schemas import NoteResponse
from .utils import verify_admin

router = APIRouter()


@router.get("/{chat_iid}", response_model=list[NoteResponse])
async def list_notes(
    chat_iid: PydanticObjectId,
    user: Annotated[ChatModel, Depends(get_current_user)],
) -> list[NoteResponse]:
    chat = await ChatModel.get_by_iid(chat_iid)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    await verify_admin(chat, user)

    notes = await NoteModel.get_chat_notes(chat.tid)
    return [
        NoteResponse(
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
        for note in notes
    ]


@router.get("/{chat_iid}/{note_id}", response_model=NoteResponse)
async def get_note(
    chat_iid: PydanticObjectId,
    note_id: PydanticObjectId,
    user: Annotated[ChatModel, Depends(get_current_user)],
) -> NoteResponse:
    chat = await ChatModel.get_by_iid(chat_iid)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    await verify_admin(chat, user)

    note = await NoteModel.get(note_id)
    if not note or note.chat_tid != chat.tid:
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

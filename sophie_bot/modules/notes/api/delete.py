from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.notes import NoteModel
from sophie_bot.utils.api.auth import get_current_user
from .utils import get_chat_and_verify_admin

router = APIRouter()


@router.delete("/{chat_id}/{note_name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    chat_id: int,
    note_name: str,
    user: Annotated[ChatModel, Depends(get_current_user)],
) -> Response:
    await get_chat_and_verify_admin(chat_id, user)

    note = await NoteModel.get_by_notenames(chat_id, [note_name])
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    await note.delete()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

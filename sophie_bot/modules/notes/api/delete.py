from __future__ import annotations

from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, Response, status

from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.notes import NoteModel
from sophie_bot.utils.api.auth import get_current_user
from .utils import verify_admin

router = APIRouter()


@router.delete("/{chat_iid}/{note_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_note(
    chat_iid: PydanticObjectId,
    note_id: PydanticObjectId,
    user: Annotated[ChatModel, Depends(get_current_user)],
) -> Response:
    chat = await ChatModel.get_by_iid(chat_iid)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")
    await verify_admin(chat, user)

    note = await NoteModel.get(note_id)
    if not note or note.chat_tid != chat.tid:
        raise HTTPException(status_code=404, detail="Note not found")

    await note.delete()
    return Response(status_code=status.HTTP_204_NO_CONTENT)

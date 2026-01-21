from __future__ import annotations


from beanie import PydanticObjectId
from fastapi import APIRouter, HTTPException

from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.privatenotes import PrivateNotesModel
from .schemas import PMNotesStateResponse, PMNotesStateUpdate

router = APIRouter(prefix="/pmnotes")


@router.get("/{chat_iid}", response_model=PMNotesStateResponse)
async def get_pmnotes_state(
    chat_iid: PydanticObjectId,
) -> PMNotesStateResponse:
    chat = await ChatModel.get(chat_iid)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    enabled = await PrivateNotesModel.get_state(chat_iid)
    return PMNotesStateResponse(enabled=enabled)


@router.patch("/{chat_iid}", response_model=PMNotesStateResponse)
async def update_pmnotes_state(
    chat_iid: PydanticObjectId,
    update: PMNotesStateUpdate,
) -> PMNotesStateResponse:
    chat = await ChatModel.get(chat_iid)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    await PrivateNotesModel.set_state(chat_iid, update.enabled)

    return PMNotesStateResponse(enabled=update.enabled)

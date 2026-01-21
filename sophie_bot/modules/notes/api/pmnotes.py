from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.privatenotes import PrivateNotesModel
from sophie_bot.utils.api.auth import rest_require_admin
from .schemas import PMNotesStateResponse, PMNotesStateUpdate

router = APIRouter()


@router.get("/pmnotes/{chat_tid}", response_model=PMNotesStateResponse)
async def get_pmnotes_state(
    chat_tid: int,
    current_user: Annotated[ChatModel, Depends(rest_require_admin())],
) -> PMNotesStateResponse:
    chat = await ChatModel.get_by_tid(chat_tid)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    enabled = await PrivateNotesModel.get_state(chat_tid)
    return PMNotesStateResponse(enabled=enabled)


@router.patch("/pmnotes/{chat_tid}", response_model=PMNotesStateResponse)
async def update_pmnotes_state(
    chat_tid: int,
    update: PMNotesStateUpdate,
    current_user: Annotated[ChatModel, Depends(rest_require_admin())],
) -> PMNotesStateResponse:
    chat = await ChatModel.get_by_tid(chat_tid)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    await PrivateNotesModel.set_state(chat_tid, update.enabled)

    return PMNotesStateResponse(enabled=update.enabled)

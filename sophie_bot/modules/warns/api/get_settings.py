from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.warns import WarnSettingsModel
from sophie_bot.utils.api.auth import get_current_user
from .schemas import WarnSettingsResponse

router = APIRouter(prefix="/warns", tags=["warns"])


@router.get("/settings/{chat_tid}", response_model=WarnSettingsResponse)
async def get_warn_settings(
    chat_tid: int,
    current_user: Annotated[ChatModel, Depends(get_current_user)],
) -> WarnSettingsResponse:
    chat = await ChatModel.get_by_tid(chat_tid)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    settings = await WarnSettingsModel.get_or_create(chat.iid)
    return WarnSettingsResponse(
        max_warns=settings.max_warns, actions=[action.model_dump() for action in settings.actions]
    )

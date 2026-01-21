from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException

from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.warns import WarnSettingsModel
from sophie_bot.utils.api.auth import rest_require_admin
from .schemas import WarnSettingsResponse, WarnSettingsUpdate

router = APIRouter(prefix="/warns", tags=["warns"])


@router.patch("/settings/{chat_iid}", response_model=WarnSettingsResponse)
async def update_warn_settings(
    chat_iid: PydanticObjectId,
    update: WarnSettingsUpdate,
    current_user: Annotated[ChatModel, Depends(rest_require_admin("can_restrict_members"))],
) -> WarnSettingsResponse:
    chat = await ChatModel.get_by_iid(chat_iid)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    settings = await WarnSettingsModel.get_or_create(chat.iid)

    if update.max_warns is not None:
        settings.max_warns = update.max_warns

    await settings.save()

    return WarnSettingsResponse(
        max_warns=settings.max_warns, actions=[action.model_dump() for action in settings.actions]
    )

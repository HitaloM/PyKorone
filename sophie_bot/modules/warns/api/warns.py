from typing import Annotated, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.warns import WarnModel, WarnSettingsModel
from sophie_bot.utils.api.auth import get_current_user, rest_require_admin

router = APIRouter(prefix="/warns", tags=["warns"])


class WarnResponse(BaseModel):
    id: str
    user_id: int
    admin_id: int
    reason: Optional[str]
    date: str


class WarnSettingsResponse(BaseModel):
    max_warns: int
    actions: List[dict]


class WarnSettingsUpdate(BaseModel):
    max_warns: Optional[int] = Field(None, ge=2, le=10000)


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


@router.patch("/settings/{chat_tid}", response_model=WarnSettingsResponse)
async def update_warn_settings(
    chat_tid: int,
    update: WarnSettingsUpdate,
    current_user: Annotated[ChatModel, Depends(rest_require_admin("can_restrict_members"))],
) -> WarnSettingsResponse:
    chat = await ChatModel.get_by_tid(chat_tid)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    settings = await WarnSettingsModel.get_or_create(chat.iid)

    if update.max_warns is not None:
        settings.max_warns = update.max_warns

    await settings.save()

    return WarnSettingsResponse(
        max_warns=settings.max_warns, actions=[action.model_dump() for action in settings.actions]
    )


@router.get("/{chat_tid}/{user_tid}", response_model=List[WarnResponse])
async def get_user_warns(
    chat_tid: int,
    user_tid: int,
    current_user: Annotated[ChatModel, Depends(get_current_user)],
) -> List[WarnResponse]:
    chat = await ChatModel.get_by_tid(chat_tid)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    warns = await WarnModel.get_user_warns(chat.iid, user_tid)

    return [
        WarnResponse(
            id=str(warn.id),
            user_id=warn.user_id,
            admin_id=warn.admin_id,
            reason=warn.reason,
            date=warn.date.isoformat(),
        )
        for warn in warns
    ]

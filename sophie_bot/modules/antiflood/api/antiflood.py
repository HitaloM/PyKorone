from __future__ import annotations

from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from sophie_bot.db.models.antiflood import AntifloodModel
from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.chat_admin import ChatAdminModel
from sophie_bot.db.models.filters import FilterActionType
from sophie_bot.utils.api.auth import get_current_user

router = APIRouter(prefix="/antiflood", tags=["antiflood"])


class ActionRequest(BaseModel):
    name: str
    data: dict = Field(default_factory=dict)


class AntifloodSettingsRequest(BaseModel):
    enabled: bool = True
    message_count: int = Field(default=5, ge=1, le=100)
    actions: list[ActionRequest] = Field(default_factory=list)


class ActionResponse(BaseModel):
    name: str
    data: dict


class AntifloodSettingsResponse(BaseModel):
    chat_iid: PydanticObjectId
    chat_tid: int
    enabled: bool
    message_count: int
    actions: list[ActionResponse]


async def verify_chat_admin(
    user: ChatModel,
    chat_iid: PydanticObjectId,
) -> ChatModel:
    """Verify that the user is an admin in the specified chat."""
    admin = await ChatAdminModel.find_one(
        ChatAdminModel.chat.id == chat_iid,  # type: ignore[attr-defined]
        ChatAdminModel.user.id == user.iid,  # type: ignore[attr-defined]
    )
    if not admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not an admin in this chat",
        )
    chat = await ChatModel.get_by_iid(chat_iid)
    if not chat:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Chat not found",
        )
    return chat


@router.get("/{chat_iid}", response_model=AntifloodSettingsResponse)
async def get_antiflood_settings(
    chat_iid: PydanticObjectId,
    user: Annotated[ChatModel, Depends(get_current_user)],
) -> AntifloodSettingsResponse:
    """Get antiflood settings for a chat."""
    chat = await verify_chat_admin(user, chat_iid)

    settings = await AntifloodModel.find_one(AntifloodModel.chat.id == chat_iid)

    if not settings:
        return AntifloodSettingsResponse(
            chat_iid=chat_iid,
            chat_tid=chat.tid,
            enabled=False,
            message_count=5,
            actions=[],
        )

    return AntifloodSettingsResponse(
        chat_iid=chat_iid,
        chat_tid=chat.tid,
        enabled=settings.enabled or False,
        message_count=settings.message_count,
        actions=[ActionResponse(name=action.name, data=action.data or {}) for action in settings.actions],
    )


@router.put("/{chat_iid}", response_model=AntifloodSettingsResponse)
async def update_antiflood_settings(
    chat_iid: PydanticObjectId,
    request: AntifloodSettingsRequest,
    user: Annotated[ChatModel, Depends(get_current_user)],
) -> AntifloodSettingsResponse:
    """Update antiflood settings for a chat."""
    chat = await verify_chat_admin(user, chat_iid)

    settings = await AntifloodModel.find_one(AntifloodModel.chat.id == chat_iid)

    if not settings:
        settings = AntifloodModel(chat=chat)

    settings.enabled = request.enabled
    settings.message_count = request.message_count
    settings.actions = [FilterActionType(name=action.name, data=action.data) for action in request.actions]
    settings.action = None  # Clear legacy action

    await settings.save()

    return AntifloodSettingsResponse(
        chat_iid=chat_iid,
        chat_tid=chat.tid,
        enabled=settings.enabled or False,
        message_count=settings.message_count,
        actions=[ActionResponse(name=action.name, data=action.data or {}) for action in settings.actions],
    )


@router.delete("/{chat_iid}", status_code=status.HTTP_204_NO_CONTENT)
async def disable_antiflood(
    chat_iid: PydanticObjectId,
    user: Annotated[ChatModel, Depends(get_current_user)],
) -> None:
    """Disable antiflood for a chat (deletes settings)."""
    await verify_chat_admin(user, chat_iid)

    settings = await AntifloodModel.find_one(AntifloodModel.chat.id == chat_iid)
    if settings:
        await settings.delete()

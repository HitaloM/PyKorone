from __future__ import annotations

from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException

from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.disabling import DisablingModel
from sophie_bot.modules.help.utils.extract_info import DISABLEABLE_CMDS
from sophie_bot.utils.api.auth import get_current_user

from .schemas import DisableableResponse, DisabledResponse

router = APIRouter()


@router.get("/disabled/{chat_iid}", response_model=DisabledResponse)
async def get_disabled_commands(
    chat_iid: PydanticObjectId,
    user: Annotated[ChatModel, Depends(get_current_user)],
):
    chat = await ChatModel.get_by_iid(chat_iid)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    disabled = await DisablingModel.get_disabled(chat.tid)
    return DisabledResponse(disabled=disabled)


@router.get("/disableable", response_model=DisableableResponse)
async def get_disableable_commands(
    user: Annotated[ChatModel, Depends(get_current_user)],
):
    disableable = sorted(list(set(cmd.cmds[0] for cmd in DISABLEABLE_CMDS if cmd.cmds)))
    return DisableableResponse(disableable=disableable)

from __future__ import annotations

from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException

from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.rules import RulesModel
from sophie_bot.utils.api.auth import get_current_user

from .schemas import RulesResponse

router = APIRouter()


@router.get("/{chat_iid}", response_model=RulesResponse)
async def get_rules(
    chat_iid: PydanticObjectId,
    user: Annotated[ChatModel, Depends(get_current_user)],
):
    chat = await ChatModel.get_by_iid(chat_iid)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if rules := await RulesModel.get_rules(chat.tid):
        return RulesResponse.model_validate(rules)
    return RulesResponse()

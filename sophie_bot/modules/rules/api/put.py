from __future__ import annotations

from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException

from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.notes import Saveable
from sophie_bot.db.models.rules import RulesModel
from sophie_bot.utils.api.auth import rest_require_admin

from .schemas import RulesPayload, RulesResponse

router = APIRouter()


@router.put("/{chat_iid}", response_model=RulesResponse)
async def set_rules(
    chat_iid: PydanticObjectId,
    payload: RulesPayload,
    user: Annotated[ChatModel, Depends(rest_require_admin(permission="can_change_info"))],
):
    chat = await ChatModel.get_by_iid(chat_iid)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    if not payload.text and not payload.buttons:
        await RulesModel.del_rules(chat.tid)
        return RulesResponse()

    saveable = Saveable(text=payload.text or "", buttons=payload.buttons, preview=payload.preview)
    rules = await RulesModel.set_rules(chat.tid, saveable)
    return RulesResponse.model_validate(rules)

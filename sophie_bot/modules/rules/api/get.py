from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends

from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.rules import RulesModel
from sophie_bot.utils.api.auth import get_current_user

from .schemas import RulesResponse

router = APIRouter()


@router.get("/", response_model=RulesResponse)
async def get_rules(
    chat_tid: int,
    user: Annotated[ChatModel, Depends(get_current_user)],
):
    if rules := await RulesModel.get_rules(chat_tid):
        return RulesResponse.model_validate(rules)
    return RulesResponse()

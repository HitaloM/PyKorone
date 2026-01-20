from typing import Annotated, List

from fastapi import APIRouter, Depends, HTTPException

from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.warns import WarnModel
from sophie_bot.utils.api.auth import get_current_user
from .schemas import WarnResponse

router = APIRouter(prefix="/warns", tags=["warns"])


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

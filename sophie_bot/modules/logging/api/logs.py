from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel

from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.chat_admin import ChatAdminModel
from sophie_bot.db.models.log import LogModel
from sophie_bot.modules.logging.events import LOG_EVENT_STRINGS
from sophie_bot.utils.api.auth import get_current_user

router = APIRouter(prefix="/logging", tags=["logging"])


class LogResponse(BaseModel):
    id: str
    user_id: int
    user_name: str
    event: str
    event_display: str
    timestamp: datetime
    details: dict


@router.get("/{chat_id}", response_model=List[LogResponse])
async def get_chat_logs(
    chat_id: int,
    user: ChatModel = Depends(get_current_user),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
):
    target_chat = await ChatModel.get_by_tid(chat_id)
    if not target_chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    is_allowed = False
    if user.tid == chat_id:
        is_allowed = True
    else:
        admin = await ChatAdminModel.find_one(
            ChatAdminModel.chat.id == target_chat.iid,  # type: ignore
            ChatAdminModel.user.id == user.iid,  # type: ignore
        )
        if admin:
            is_allowed = True

    if not is_allowed:
        raise HTTPException(status_code=403, detail="Not authorized")

    logs = (
        await LogModel.find(LogModel.chat.id == target_chat.iid, fetch_links=True)
        .sort("-timestamp")
        .skip(offset)
        .limit(limit)
        .to_list()
    )

    response = []
    for log in logs:
        user_name = "Unknown"
        user_id = 0

        if log.user and isinstance(log.user, ChatModel):
            user_name = log.user.first_name_or_title
            user_id = log.user.tid

        response.append(
            LogResponse(
                id=str(log.id),
                user_id=user_id,
                user_name=user_name,
                event=log.event,
                event_display=str(LOG_EVENT_STRINGS.get(log.event, log.event)),
                timestamp=log.timestamp,
                details=log.details,
            )
        )

    return response

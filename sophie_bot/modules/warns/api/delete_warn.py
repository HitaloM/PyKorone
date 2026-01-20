from typing import Annotated

from beanie import PydanticObjectId
from fastapi import APIRouter, Depends, HTTPException

from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.warns import WarnModel
from sophie_bot.utils.api.auth import rest_require_admin

router = APIRouter(prefix="/warns", tags=["warns"])


@router.delete("/{chat_tid}/{warn_iid}")
async def delete_warn(
    chat_tid: int,
    warn_iid: str,
    current_user: Annotated[ChatModel, Depends(rest_require_admin("can_restrict_members"))],
) -> dict:
    chat = await ChatModel.get_by_tid(chat_tid)
    if not chat:
        raise HTTPException(status_code=404, detail="Chat not found")

    try:
        warn_obj_id = PydanticObjectId(warn_iid)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid warn_iid")

    warn = await WarnModel.find_one(WarnModel.id == warn_obj_id, WarnModel.chat.iid == chat.iid)
    if not warn:
        raise HTTPException(status_code=404, detail="Warning not found")

    await warn.delete()
    return {"status": "ok"}

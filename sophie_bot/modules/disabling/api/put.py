from __future__ import annotations

from typing import Annotated

from beanie.odm.operators.update.general import Set
from fastapi import APIRouter, Depends

from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.disabling import DisablingModel
from sophie_bot.modules.help.utils.extract_info import DISABLEABLE_CMDS
from sophie_bot.utils.api.auth import rest_require_admin

from .schemas import DisabledPayload, DisabledResponse

router = APIRouter()


@router.put("/disabled", response_model=DisabledResponse)
async def set_disabled_commands(
    chat_tid: int,
    payload: DisabledPayload,
    user: Annotated[ChatModel, Depends(rest_require_admin(permission="can_change_info"))],
):
    # Filter to only allow disableable commands
    disableable = set(cmd.cmds[0] for cmd in DISABLEABLE_CMDS if cmd.cmds)
    to_disable = [cmd for cmd in payload.disabled if cmd in disableable]

    await DisablingModel.find_one(DisablingModel.chat_id == chat_tid).upsert(
        Set({DisablingModel.cmds: to_disable}),
        on_insert=DisablingModel(chat_id=chat_tid, cmds=to_disable),
    )
    return DisabledResponse(disabled=to_disable)

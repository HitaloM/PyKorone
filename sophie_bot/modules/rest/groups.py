from __future__ import annotations

from typing import Annotated

from aiogram.types import ResultChatMemberUnion
from beanie import Link
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from sophie_bot.db.models.chat import ChatModel
from sophie_bot.db.models.chat_admin import ChatAdminModel
from sophie_bot.utils.api.auth import get_current_user

router = APIRouter(prefix="/groups", tags=["groups"])


class GroupResponse(BaseModel):
    chat_id: int
    title: str
    username: str | None
    photo_url: str | None
    permissions: ResultChatMemberUnion


@router.get("", response_model=list[GroupResponse])
async def get_user_groups(
    user: Annotated[ChatModel, Depends(get_current_user)],
) -> list[GroupResponse]:
    admins = (
        await ChatAdminModel.find(
            ChatAdminModel.user.id == user.id,  # type: ignore[attr-defined]
        )
        .find_many()
        .to_list()
    )

    response = []
    for admin in admins:
        chat = await admin.chat.fetch()
        if not chat or isinstance(chat, Link):
            continue

        response.append(
            GroupResponse(
                chat_id=chat.chat_id,
                title=chat.first_name_or_title,
                username=chat.username,
                photo_url=chat.photo_url,
                permissions=admin.member,
            )
        )

    return response

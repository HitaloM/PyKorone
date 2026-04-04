from __future__ import annotations

from typing import TYPE_CHECKING, Any, Required, TypedDict, cast

if TYPE_CHECKING:
    from aiogram.fsm.context import FSMContext
    from aiogram.types import Chat, User

    from korone.db.models.chat import ChatModel, UserInGroupModel
    from korone.middlewares.chat_context import ChatContext


class KoroneContextData(TypedDict, total=False):
    event_chat: Chat
    event_from_user: User
    chat: Required[ChatContext]
    chat_db: ChatModel | None
    group_db: ChatModel | None
    user_db: ChatModel | None
    user_in_group: UserInGroupModel | None
    state: Required[FSMContext]
    updated_chats: list[Chat | User]
    new_users: list[ChatModel]


def as_korone_context(data: dict[str, Any]) -> KoroneContextData:
    return cast("KoroneContextData", data)


def get_chat_db(data: dict[str, Any]) -> ChatModel | None:
    context = as_korone_context(data)
    group_db = context.get("group_db")
    if group_db is not None:
        return group_db
    return context.get("chat_db")

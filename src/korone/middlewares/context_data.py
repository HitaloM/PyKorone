from typing import TYPE_CHECKING, Any, Required, cast

from aiogram.dispatcher.middlewares.data import MiddlewareData

if TYPE_CHECKING:
    from aiogram.types import Chat, User

    from korone.db.models.chat import ChatModel, UserInGroupModel
    from korone.middlewares.chat_context import ChatContext


class KoroneContextData(MiddlewareData, total=False):
    chat: Required[ChatContext]
    chat_db: ChatModel | None
    group_db: ChatModel | None
    user_db: ChatModel | None
    user_in_group: UserInGroupModel | None
    updated_chats: list[Chat | User]
    new_users: list[ChatModel]


def as_korone_context(data: dict[str, Any]) -> KoroneContextData:
    return cast("KoroneContextData", data)


def get_chat_db(context: KoroneContextData) -> ChatModel | None:
    group_db = context.get("group_db")
    if group_db is not None:
        return group_db
    return context.get("chat_db")

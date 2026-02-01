from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram.types import User
from attr import dataclass

from korone.db.models.chat import ChatModel
from korone.modules.utils_.message import is_real_reply
from korone.utils.exception import KoroneException

if TYPE_CHECKING:
    from aiogram.types import Message

    from korone.utils.handlers import HandlerData


@dataclass(frozen=True, slots=True)
class UnionUser:
    chat_id: int
    first_name: str
    last_name: str | None
    username: str | None


def get_arg_or_reply_user(message: Message, data: HandlerData) -> User | ChatModel:
    if not message.from_user:
        raise KoroneException("No from_user")

    if message.reply_to_message and is_real_reply(message) and message.reply_to_message.from_user:
        return message.reply_to_message.from_user
    elif db_user := data.get("user"):
        if isinstance(db_user, ChatModel):
            return db_user
        raise KoroneException("Invalid user data")
    else:
        raise KoroneException("No user found")


def get_union_user(user: User | ChatModel) -> UnionUser:
    if isinstance(user, User):
        return UnionUser(chat_id=user.id, first_name=user.first_name, last_name=user.last_name, username=user.username)
    elif isinstance(user, ChatModel):
        return UnionUser(
            chat_id=user.id, first_name=user.first_name_or_title, last_name=user.last_name, username=user.username
        )
    else:
        raise ValueError("Invalid user type to cast to UnionUser")

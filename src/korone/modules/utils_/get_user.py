from __future__ import annotations

from typing import TYPE_CHECKING

from aiogram.types import User
from attr import dataclass

from korone.db.models.chat import ChatModel
from korone.modules.utils_.message import is_real_reply
from korone.utils.exception import KoroneError

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
        msg = "No from_user"
        raise KoroneError(msg)

    if message.reply_to_message and is_real_reply(message) and message.reply_to_message.from_user:
        return message.reply_to_message.from_user
    if db_user := data.get("user"):
        if isinstance(db_user, ChatModel):
            return db_user
        msg = "Invalid user data"
        raise KoroneError(msg)
    msg = "No user found"
    raise KoroneError(msg)


def get_union_user(user: User | ChatModel) -> UnionUser:
    if isinstance(user, User):
        return UnionUser(chat_id=user.id, first_name=user.first_name, last_name=user.last_name, username=user.username)
    if isinstance(user, ChatModel):
        return UnionUser(
            chat_id=user.id, first_name=user.first_name_or_title, last_name=user.last_name, username=user.username
        )
    msg = "Invalid user type to cast to UnionUser"
    raise ValueError(msg)

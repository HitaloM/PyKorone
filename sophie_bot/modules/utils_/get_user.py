from typing import Any, Optional

from aiogram.types import Message, User
from attr import dataclass

from sophie_bot.db.models import ChatModel
from sophie_bot.modules.utils_.message import is_real_reply
from sophie_bot.utils.exception import SophieException


@dataclass
class UnionUser:
    chat_id: int
    first_name: str
    last_name: Optional[str]
    username: Optional[str]


def get_arg_or_reply_user(message: Message, data: dict[str, Any]) -> User | ChatModel:
    if not message.from_user:
        raise SophieException("No from_user")

    if message.reply_to_message and is_real_reply(message) and message.reply_to_message.from_user:
        return message.reply_to_message.from_user
    elif db_user := data.get("user"):
        return db_user
    else:
        raise SophieException("No user found")


def get_union_user(user: User | ChatModel) -> UnionUser:
    if isinstance(user, User):
        return UnionUser(
            chat_id=user.id,
            first_name=user.first_name,
            last_name=user.last_name,
            username=user.username,
        )
    elif isinstance(user, ChatModel):
        return UnionUser(
            chat_id=user.tid, first_name=user.first_name_or_title, last_name=user.last_name, username=user.username
        )
    else:
        raise ValueError("Invalid user type to cast to UnionUser")

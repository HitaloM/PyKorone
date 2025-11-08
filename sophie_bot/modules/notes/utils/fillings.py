import html
from typing import Optional

from aiogram.types import Message, User
from stfu_tg import EscapedStr, HList, UserLink

from sophie_bot.utils.i18n import gettext as _


def chat_fillings(text: str, message: Optional[Message]) -> str:
    if not message:
        return text
    chat_id = message.chat.id
    chat_name = html.escape(message.chat.title or _("Local chat"), quote=False)

    return (
        text.replace("{chatid}", str(chat_id))
        .replace("{chatname}", str(chat_name))
        .replace("{chatnick}", str(message.chat.username or chat_name))
    )


def user_fillings(text: str, message: Optional[Message], user: Optional[User]) -> str:
    if not user:
        return text

    users: list[User] = (message.new_chat_members if message else None) or [user]

    return (
        text.replace("{first}", str(EscapedStr(user.first_name)))
        .replace("{last}", str(EscapedStr(user.last_name or "")))
        .replace("{fullname}", f"{user.first_name} {user.last_name}")
        .replace("{id}", str(user.id))
        .replace("{username}", user.first_name or user.first_name)
        .replace(
            "{mention}",
            str(HList(*(UserLink(user.id, user.first_name) for user in users), divider=",")),
        )
    )


def custom_fillings(text: str, additional_fillings: Optional[dict[str, str]]):
    if not additional_fillings:
        return text

    for filling in additional_fillings.items():
        text = text.replace("{" + filling[0] + "}", filling[1])

    return text


def process_fillings(
    text: str, message: Optional[Message], user: Optional[User], additional_fillings: Optional[dict[str, str]] = None
) -> str:
    if not text:
        return text

    text = chat_fillings(text, message)
    text = user_fillings(text, message, user)
    text = custom_fillings(text, additional_fillings)

    return text

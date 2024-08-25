# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import html
import re

from hydrogram.enums import ParseMode
from hydrogram.types import Message, User

from korone.utils.i18n import gettext as _

RANDOM_REGEXP = re.compile(r"{([^{}]+)}")


def get_user_details(user: User, message: Message) -> dict:
    first_name = html.escape(user.first_name, quote=False)  # type: ignore
    last_name = html.escape(user.last_name or "", quote=False)
    user_id = (
        next(user.id for user in message.new_chat_members) if message.new_chat_members else user.id
    )

    if message.new_chat_members and message.new_chat_members[0].username:
        username = f"@{message.new_chat_members[0].username}"
    elif user.username:
        username = f"@{user.username}"
    else:
        username = user.first_name

    return {
        "first_name": first_name,
        "last_name": last_name,
        "full_name": user.full_name,
        "user_id": user_id,
        "username": username,
        "mention": user.mention(style=ParseMode.HTML),  # type: ignore
    }


def get_chat_details(message: Message) -> dict:
    chat_id = message.chat.id
    chat_name = html.escape(message.chat.title or _("private chat"), quote=False)
    chat_nick = message.chat.username or chat_name

    return {"chat_id": chat_id, "chat_name": chat_name, "chat_nick": chat_nick}


def vars_parser(text: str, message: Message, user: User) -> str:
    if not text:
        return text

    user_details = get_user_details(user, message)
    chat_details = get_chat_details(message)

    return (
        text.replace("{first}", user_details["first_name"])
        .replace("{last}", user_details["last_name"])
        .replace("{fullname}", str(user_details["full_name"]))
        .replace("{id}", str(user_details["user_id"]))
        .replace("{userid}", str(user_details["user_id"]))
        .replace("{username}", user_details["username"])
        .replace("{chatid}", str(chat_details["chat_id"]))
        .replace("{chatname}", chat_details["chat_name"])
        .replace("{chatnick}", chat_details["chat_nick"])
        .replace("{mention}", user_details["mention"])
    )

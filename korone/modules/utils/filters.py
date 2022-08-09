# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

import html
from datetime import datetime
from typing import List

from babel.dates import format_date, format_datetime, format_time
from pyrogram.enums import ParseMode
from pyrogram.types import Message, User

from korone.database.filters import get_all_filters
from korone.modules.utils.languages import get_chat_lang

SMART_OPEN = "“"
SMART_CLOSE = "”"
START_CHAR = ("'", '"', SMART_OPEN)


def remove_escapes(text: str) -> str:
    counter = 0
    res = ""
    is_escaped = False
    while counter < len(text):
        if is_escaped:
            res += text[counter]
            is_escaped = False
        elif text[counter] == "\\":
            is_escaped = True
        else:
            res += text[counter]
        counter += 1
    return res


def split_quotes(text: str) -> List:
    if any(text.startswith(char) for char in START_CHAR):
        counter = 1  # ignore first char -> is some kind of quote
        while counter < len(text):
            if text[counter] == "\\":
                counter += 1
            elif text[counter] == text[0] or (
                text[0] == SMART_OPEN and text[counter] == SMART_CLOSE
            ):
                break
            counter += 1
        else:
            return text.split(None, 1)

        # 1 to avoid starting quote, and counter is exclusive so avoids ending
        key = remove_escapes(text[1:counter].strip())
        # index will be in range, or `else` would have been executed and returned
        rest = text[counter + 1 :].strip()
        if not key:
            key = text[0] + text[0]
        return list(filter(None, [key, rest]))
    else:
        return text.split(None, 1)


async def vars_parser(text: str, message: Message, user: User = None):
    if not text:
        return text

    language_code = await get_chat_lang(user.id)
    current_datetime = datetime.now()

    first_name = html.escape(user.first_name, quote=False)
    last_name = html.escape(user.last_name or "", quote=False)
    mention = user.mention(user.first_name, style=ParseMode.MARKDOWN)

    if user.username:
        username = "@" + user.username
    else:
        username = mention

    chat_id = message.chat.id
    chat_name = html.escape(message.chat.title or "Local", quote=False)
    chat_nick = message.chat.username or chat_name

    current_date = html.escape(
        format_date(date=current_datetime, locale=language_code), quote=False
    )
    current_time = html.escape(
        format_time(time=current_datetime, locale=language_code), quote=False
    )
    current_timedate = html.escape(
        format_datetime(datetime=current_datetime, locale=language_code), quote=False
    )

    text = (
        text.replace("{first}", first_name)
        .replace("{last}", last_name)
        .replace("{fullname}", first_name + " " + last_name)
        .replace("{id}", str(user.id))
        .replace("{userid}", str(user.id))
        .replace("{mention}", mention)
        .replace("{username}", username)
        .replace("{chatid}", str(chat_id))
        .replace("{chatname}", str(chat_name))
        .replace("{chatnick}", str(chat_nick))
        .replace("{date}", str(current_date))
        .replace("{time}", str(current_time))
        .replace("{timedate}", str(current_timedate))
    )
    return text


async def check_for_filters(chat_id: int, handler: str):
    filters = await get_all_filters(chat_id)
    for rfilter in filters:
        keyword = rfilter[1]
        if handler == keyword:
            return True
    return False

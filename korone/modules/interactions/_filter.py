# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2022 Amano Team
#
# This file is part of Korone (Telegram Bot)

import re
from typing import Callable, Optional

from pyrogram import Client, filters
from pyrogram.types import Message

from korone.modules import COMMANDS_HELP
from korone.utils.langs.decorators import chat_languages, languages, user_languages
from korone.utils.langs.methods import get_chat_lang, get_user_lang


def interactions_filter(
    filter: str,
    translate: Optional[bool] = True,
    group: Optional[str] = "others",
    action: Optional[str] = None,
    *args,
    **kwargs,
) -> Callable:
    async def func(flt, client: Client, message: Message):
        if not message.text:
            return False

        if translate is True:
            chat = message.chat
            if chat.type == "private":
                user_id = message.from_user.id
                await get_user_lang(user_id)
                message._lang = languages[user_languages[user_id]]
            else:
                chat_id = chat.id
                await get_chat_lang(chat_id)
                message._lang = languages[chat_languages[chat_id]]

            lang = message._lang

            string = lang.strings[lang.code][filter + "_filter"]
            # COMMANDS_HELP[group]["filters"][string] = {"action": action or " "}
            intfilter = rf"(?i)^{re.escape(string)}(\.|\?|\!)?$"
        else:
            intfilter = rf"(?i)^{re.escape(filter)}(\.|\?|\!)?$"

        return bool(
            re.match(
                intfilter,
                message.text,
            )
        )

    COMMANDS_HELP[group]["filters"][filter] = {"action": action or " "}

    return filters.create(
        func,
        "InteractionsFilter",
    )


filters.int = interactions_filter

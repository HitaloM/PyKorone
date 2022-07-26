# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

import logging
import os
from typing import Dict, Union

import yaml
from babel.core import Locale
from pyrogram import Client
from pyrogram.enums import ChatType
from pyrogram.types import CallbackQuery, InlineQuery, Message

from korone.bot import Korone
from korone.database.chats import get_chat_by_id
from korone.database.languages import change_chat_lang, change_user_lang
from korone.database.users import get_user_by_id

logger = logging.getLogger(__name__)

LANGUAGES: Dict = {}

logger.info("[%s] Loading locales...", Korone.__name__)

for filename in os.listdir("korone/locales"):
    logger.debug("Loading language file " + filename)
    with open("korone/locales/" + filename, "r", encoding="utf8") as f:
        lang = yaml.load(f, Loader=yaml.CLoader)

        lang_code = lang["language_info"]["code"]
        lang["language_info"]["babel"] = Locale(lang_code)

        LANGUAGES[lang_code] = lang

logger.info(
    "[%s] Languages loaded: %s",
    Korone.__name__,
    [
        language["language_info"]["babel"].display_name
        for language in LANGUAGES.values()
    ],
)


async def get_chat_lang(chat_id):
    chat_lang = await get_chat_by_id(chat_id)
    if chat_lang:
        return chat_lang["language"]

    user_lang = await get_user_by_id(chat_id)
    if not user_lang or user_lang["language"] not in LANGUAGES:
        print(chat_id)
        return "en"

    return user_lang["language"]


async def get_strings(chat_id, module, mas_name="STRINGS"):
    chat_lang = await get_chat_lang(chat_id)
    if chat_lang not in LANGUAGES:
        if str(chat_id).startswith("-100"):
            await change_chat_lang(chat_id, "en")
        else:
            await change_user_lang(chat_id, "en")

    class Strings:
        @staticmethod
        def get_strings(lang, mas_name, module):

            if (
                mas_name not in LANGUAGES[lang]
                or module not in LANGUAGES[lang][mas_name]
            ):
                return {}

            data = LANGUAGES[lang][mas_name][module]

            if mas_name == "STRINGS":
                data["language_info"] = LANGUAGES[chat_lang]["language_info"]
            return data

        def get_string(self, name):
            data = self.get_strings(chat_lang, mas_name, module)
            if name not in data:
                data = self.get_strings("en", mas_name, module)

            return data[name]

        def __getitem__(self, key):
            return self.get_string(key)

    return Strings()


async def get_string(chat_id, module, name, mas_name="STRINGS"):
    strings = await get_strings(chat_id, module, mas_name=mas_name)
    return strings[name]


def get_strings_dec(module, mas_name="STRINGS"):
    def decorator(func):
        async def wrapper(
            client: Client,
            union: Union[CallbackQuery, InlineQuery, Message],
            *args,
            **kwargs
        ):
            message = union.message if isinstance(union, CallbackQuery) else union
            if not isinstance(union, InlineQuery):
                chat = message.chat

            chat_id = None
            if isinstance(union, InlineQuery) or chat.type == ChatType.PRIVATE:
                chat_id = union.from_user.id
            else:
                chat_id = chat.id

            strings = await get_strings(chat_id, module, mas_name=mas_name)
            return await func(client, union, strings, *args, **kwargs)

        return wrapper

    return decorator


async def get_chat_lang_info(chat_id):
    chat_lang = await get_chat_lang(chat_id)
    return LANGUAGES[chat_lang]["language_info"]


__help__ = True

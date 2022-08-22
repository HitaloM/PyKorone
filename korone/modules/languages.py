# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

from contextlib import suppress
from typing import List, Tuple, Union

from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.errors import MessageNotModified
from pyrogram.helpers import array_chunk, bki, ikb
from pyrogram.types import CallbackQuery, Message

from ..bot import Korone
from ..database.languages import change_chat_lang, change_user_lang
from ..utils.languages import LANGUAGES, get_chat_lang_info, get_strings_dec


@Korone.on_message(filters.cmd("language"))
@Korone.on_callback_query(filters.regex(r"^language$"))
@get_strings_dec("languages")
async def language(bot: Korone, union: Union[Message, CallbackQuery], strings):
    message = union.message if isinstance(union, CallbackQuery) else union
    chat = message.chat
    if isinstance(union, Message):
        if chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
            if not await filters.admin(bot, union):
                await union.reply_text(strings["not_admin"])
                return

    lang_info = await get_chat_lang_info(chat.id)

    buttons: List[Tuple] = []
    for lang in LANGUAGES.values():
        nlang = lang["language_info"]
        text, data = (
            f"{nlang['flag']} {nlang['babel'].display_name}",
            f"language set {nlang['code']}",
        )
        buttons.append((text, data))

    keyboard = array_chunk(buttons, 2)

    keyboard.append(
        [
            (
                strings["contrib_locale"],
                "https://crowdin.com/project/pykorone/",
                "url",
            )
        ]
    )

    if isinstance(union, CallbackQuery):
        keyboard.append([(strings["back_button"], "start")])

    await (
        union.message.edit_text
        if isinstance(union, CallbackQuery)
        else union.reply_text
    )(
        strings["language_text"].format(lang_name=lang_info["babel"].display_name),
        reply_markup=ikb(keyboard),
    )


@Korone.on_callback_query(filters.regex(r"^language set (?P<code>\w+)"))
@get_strings_dec("languages")
async def language_set(bot: Korone, callback: CallbackQuery, strings):
    message = callback.message
    chat = message.chat
    user = callback.from_user
    language_code = callback.matches[0]["code"]

    if chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        if not await filters.admin(bot, callback):
            await callback.answer(
                strings["not_admin"],
                show_alert=True,
                cache_time=60,
            )
            return

    if chat.type == ChatType.PRIVATE:
        await change_user_lang(user.id, str(language_code))
    else:
        await change_chat_lang(chat.id, str(language_code))

    nlang = LANGUAGES[language_code]["STRINGS"]["languages"]
    lang_info = LANGUAGES[language_code]["language_info"]
    text = nlang["language_changed_alert"].format(
        lang_name=lang_info["babel"].display_name
    )

    for line in bki(message.reply_markup):
        for button in line:
            if button[0] == strings["back_button"]:
                await callback.answer(text, show_alert=True)
                with suppress(MessageNotModified):
                    await language(bot, callback)
                return

    await callback.edit_message_text(text)

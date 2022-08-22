# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

import html

from pyrogram import filters
from pyrogram.errors import MessageTooLong
from pyrogram.types import Message

from ..bot import Korone
from .utils.disable import disableable_dec
from .utils.languages import get_chat_lang, get_strings_dec
from .utils.translator import get_tr_lang, translator


@Korone.on_message(filters.cmd(["tr", "translate"]))
@disableable_dec("tr")
@get_strings_dec("translator")
async def translate(bot: Korone, message: Message, strings):
    text = message.text[4:]
    language = await get_chat_lang(message.chat.id)
    lang = get_tr_lang(text, language)

    text = text.replace(lang, "", 1).strip() if text.startswith(lang) else text

    if message.reply_to_message and not text:
        text = message.reply_to_message.text or message.reply_to_message.caption

    if not text:
        return await message.reply_text(strings["usage"])

    sent = await message.reply_text(strings["translating"])

    langs = {}
    if len(lang.split("-")) > 1:
        langs["sourcelang"] = lang.split("-")[0]
        langs["targetlang"] = lang.split("-")[1]
    else:
        langs["targetlang"] = lang

    tr = await translator(text, **langs)

    if tr.lang == langs["targetlang"]:
        await sent.edit_text(strings["why_translate_same_lang"])
        return

    try:
        await sent.edit_text(
            strings["translated"].format(
                from_lang=tr.lang,
                to_lang=langs["targetlang"],
                translated=html.escape(tr.text),
            )
        )
    except MessageTooLong:
        await sent.edit_text(strings["too_long"])


__help__ = True

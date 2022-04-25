# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2022 Amano Team
#
# This file is part of Korone (Telegram Bot)

from contextlib import suppress
from typing import Union

from pyrogram import filters
from pyrogram.enums import ChatMemberStatus, ChatType
from pyrogram.errors import MessageNotModified
from pyrogram.helpers import array_chunk, bki, ikb
from pyrogram.types import CallbackQuery, Message

from korone.database.language import update_chat_language, update_user_language
from korone.korone import Korone
from korone.utils.langs.decorators import (
    chat_languages,
    use_chat_language,
    user_languages,
)
from korone.utils.langs.methods import get_user_lang


@Korone.on_callback_query(filters.regex(r"^language$"))
@Korone.on_message(
    filters.cmd(command="language", action="Altere o idioma do chat atual.")
)
@use_chat_language()
async def language(c: Korone, m: Union[Message, CallbackQuery]):
    lang = m._lang
    if isinstance(m, Message):
        chat = m.chat
        user = m.from_user

        if chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
            member = await c.get_chat_member(chat.id, user.id)
            if member.status not in (
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.OWNER,
            ):
                await m.reply_text(
                    lang.get_language(await get_user_lang(user.id)).not_admin
                )
                return

    buttons = []
    for language_code in lang.strings.keys():
        text = f"{lang.strings[language_code]['LANGUAGE_NAME']} {lang.strings[language_code]['LANGUAGE_FLAG']}"
        data = f"language set {language_code}"
        buttons.append((text, data))

    keyboard = array_chunk(buttons, 2)

    if isinstance(m, CallbackQuery):
        keyboard.append([(lang.back_button, "start_back")])

    await (m.message.edit_text if isinstance(m, CallbackQuery) else m.reply_text)(
        lang.language_text.format(lang_name=lang.LANGUAGE_NAME),
        reply_markup=ikb(keyboard),
    )


@Korone.on_callback_query(filters.regex(r"^language set (?P<language_code>\w+)$"))
@use_chat_language()
async def language_set(c: Korone, q: CallbackQuery):
    message = q.message
    chat = message.chat
    user = q.from_user
    lang = q._lang

    if chat.type in (ChatType.GROUP, ChatType.SUPERGROUP):
        member = await c.get_chat_member(chat.id, user.id)
        if member.status not in (
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        ):
            await q.answer(
                lang.get_language(await get_user_lang(user.id)).not_admin,
                show_alert=True,
                cache_time=60,
            )
            return

    language_code = q.matches[0]["language_code"]

    if chat.type == ChatType.PRIVATE:
        await update_user_language(user.id, language_code)
        user_languages[user.id] = language_code
    else:
        await update_chat_language(chat.id, language_code)
        chat_languages[chat.id] = language_code

    nlang = lang.get_language(language_code)
    text = nlang.language_changed_alert.format(lang_name=nlang.LANGUAGE_NAME)

    for line in bki(message.reply_markup):
        for button in line:
            if button[0] == lang.back_button:
                await q.answer(text, show_alert=True)
                with suppress(MessageNotModified):
                    await language(c, q)
                return

    await q.edit_message_text(text)

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

import html

import httpx
from pyrogram import filters
from pyrogram.enums import ChatMemberStatus, ChatType
from pyrogram.errors import PeerIdInvalid, UsernameInvalid, UserNotParticipant
from pyrogram.types import Message

from korone.bot import Korone
from korone.config import config
from korone.modules.utils.disable import disableable_dec
from korone.modules.utils.languages import get_strings_dec
from korone.modules.utils.messages import get_args


@Korone.on_message(filters.cmd("user"))
@disableable_dec("user")
@get_strings_dec("users")
async def user_info(bot: Korone, message: Message, strings):
    args = get_args(message).split(" ")[0]

    if args.isdigit() or args.startswith("@"):
        try:
            user = await bot.get_users(args)
        except UsernameInvalid:
            await message.reply_text(strings["invalid_username"])
            return
        except PeerIdInvalid:
            await message.reply_text(strings["invalid_id"])
            return

    elif message.reply_to_message:
        user = message.reply_to_message.from_user
    else:
        user = message.from_user

    if user is None:
        await message.reply_text(strings["not_user"])
        return

    text = strings["user_info"]
    text += strings["user_id"].format(id=user.id)
    text += strings["user_firstname"].format(
        first_name=html.escape(user.first_name),
    )

    if user.last_name:
        text += strings["user_lastname"].format(
            last_name=html.escape(user.last_name),
        )

    if user.username:
        text += strings["username"].format(username=user.username)

    text += strings["user_link"].format(
        link=user.mention(user.first_name, style="html")
    )

    if user.photo:
        photo_count = await bot.get_chat_photos_count(user.id)
        text += strings["user_photos"].format(count=photo_count)

    if user.dc_id:
        text += strings["user_dc"].format(id=user.dc_id)
    if user.language_code:
        text += strings["user_lang"].format(lang=user.language_code)

    if bio := (await bot.get_chat(chat_id=user.id)).bio:
        text += strings["user_bio"].format(bio=html.escape(bio))

    if swkey := config.get_config("spamwatch_key"):
        async with httpx.AsyncClient(http2=True) as client:
            r = await client.get(
                f"https://api.spamwat.ch/banlist/{int(user.id)}",
                headers={"Authorization": f"Bearer {swkey}"},
            )
            if not r.status_code != 200:
                ban = r.json()
                text += strings["sw_banned"]
                text += strings["sw_banned_reason"].format(
                    reason=ban["reason"],
                )

    if message.chat.type != ChatType.PRIVATE:
        try:
            member = await bot.get_chat_member(message.chat.id, user.id)
            if member.status == ChatMemberStatus.ADMINISTRATOR:
                text += strings["user_admin"]
            elif member.status == ChatMemberStatus.OWNER:
                text += strings["user_owner"]
        except UserNotParticipant:
            pass

    if user.photo:
        async for photo in bot.get_chat_photos(chat_id=user.id, limit=1):
            await message.reply_photo(photo.file_id, caption=text)
    else:
        await message.reply_text(text, disable_web_page_preview=True)


@Korone.on_message(filters.cmd("id"))
@disableable_dec("id")
@get_strings_dec("users")
async def user_id(bot: Korone, message: Message, strings):
    user_id = message.from_user.id
    chat_id = message.chat.id

    text = strings["your_id"].format(id=user_id)
    if chat_id != user_id:
        text += strings["chat_id"].format(id=chat_id)

    if message.reply_to_message:
        if message.reply_to_message.from_user.id != user_id:
            text += strings["reply_id"].format(
                id=message.reply_to_message.from_user.id,
            )
        if message.reply_to_message.forward_from:
            user_id = message.reply_to_message.forward_from.id
            text += strings["forward_id"].format(id=user_id)

    await message.reply_text(text)


__help__ = True

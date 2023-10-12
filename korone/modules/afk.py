# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo M. <https://github.com/HitaloM>

import random
import re
from asyncio import sleep
from contextlib import suppress
from datetime import datetime

import humanize
from pyrogram import filters
from pyrogram.enums import MessageEntityType
from pyrogram.errors import BadRequest, FloodWait, Forbidden
from pyrogram.types import Message

from ..bot import Korone
from ..database.afk import is_afk, rm_afk, set_afk
from ..utils.disable import disableable_dec
from ..utils.languages import get_strings_dec
from ..utils.messages import get_args


@Korone.on_message(filters.cmd("afk") | filters.regex(r"(?i)^brb(.*)$"))
@disableable_dec("afk")
@get_strings_dec("afk")
async def afk(bot: Korone, message: Message, strings):
    if not message.from_user:
        return

    if await is_afk(message.from_user.id):
        await no_longer_afk(bot, message)
        return

    reason = get_args(message)

    if not message.from_user:
        return

    if not reason:
        reason = ""

    notice = ""
    if len(reason) > 100:
        reason = reason[:100]
        notice = strings["notice"]

    await set_afk(message.from_user.id, reason)

    sent = await message.reply_text(
        strings["now_afk"].format(
            name=message.from_user.first_name,
            notice=notice,
        )
    )

    with suppress(BadRequest, Forbidden):
        await sleep(15)
        await bot.delete_messages(
            chat_id=message.chat.id,
            message_ids=(message.id, sent.id),
        )


@Korone.on_message(~filters.private & ~filters.bot & filters.all, group=2)
@get_strings_dec("afk")
async def no_longer_afk(bot: Korone, message: Message, strings):
    if not message.from_user:
        return

    if message.text:
        afk_cmd = re.findall(r"^[!/]\bafk\b|\bbrb\b(.*)", message.text)
        if afk_cmd:
            return

    res = await rm_afk(message.from_user.id)
    if res:
        if message.new_chat_members:
            return

        chosen_option = random.choice(strings["afk_back_list"])
        sent = await message.reply_text(
            chosen_option.format(
                name=message.from_user.first_name,
            )
        )

        with suppress(BadRequest, Forbidden):
            await sleep(15)
            await sent.delete()


@Korone.on_message(~filters.private & ~filters.bot & filters.all, group=3)
@get_strings_dec("afk")
async def reply_afk(bot: Korone, message: Message, strings):
    if not message.from_user:
        return

    if entities := message.entities:
        chk_users = []
        for ent in entities:
            if ent.type == MessageEntityType.TEXT_MENTION:
                user_id = ent.user.id

                if user_id in chk_users:
                    return

                chk_users.append(user_id)

            if ent.type != MessageEntityType.MENTION:
                return

            try:
                user = await bot.get_users(
                    message.text[ent.offset: ent.offset + ent.length]
                )  # todo: use database to store and retrieve users (avoiding FloodWait)
            except (IndexError, KeyError, BadRequest, FloodWait):
                return

            if user in chk_users:
                return

            chk_users.append(user)

            try:
                chat = await bot.get_users(int(user.id))
            except BadRequest:
                return

            await check_afk(
                message,
                user.id,
                chat.first_name,
                strings,
            )
    elif message.reply_to_message and message.reply_to_message.from_user:
        await check_afk(
            message,
            message.reply_to_message.from_user.id,
            message.reply_to_message.from_user.first_name,
            strings,
        )


async def check_afk(message: Message, user_id: int, first_name: str, strings):
    if user := await is_afk(user_id):
        if message.from_user.id == user_id:
            return

        time = humanize.naturaldelta(datetime.now() - datetime.fromtimestamp(user["time"]))

        if not user["reason"]:
            res = strings["afk_reply_time"].format(
                name=first_name,
                time=time,
            )
        else:
            res = strings["afk_reply_reason"].format(
                name=first_name,
                reason=user["reason"],
                time=time,
            )

        sent = await message.reply_text(res)

        with suppress(BadRequest, Forbidden):
            await sleep(15)
            await sent.delete()


__help__ = True

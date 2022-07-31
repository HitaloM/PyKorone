# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

import asyncio
import functools
import random
import re
from string import printable

import regex
from async_timeout import timeout
from pyrogram import filters
from pyrogram.enums import ChatType, ParseMode
from pyrogram.types import Message

from korone.bot import Korone
from korone.database.filters import (
    add_filter,
    get_all_filters,
    remove_filter,
    update_filter,
)
from korone.modules.utils.filters import split_quotes, vars_parser
from korone.modules.utils.languages import get_strings_dec
from korone.modules.utils.messages import need_args_dec

loop = asyncio.get_event_loop()


async def check_for_filters(chat_id: int, handler: str):
    filters = await get_all_filters(chat_id)
    for rfilter in filters:
        keyword = rfilter[1]
        if handler == keyword:
            return True
    return False


@Korone.on_message(filters.group & filters.text & filters.incoming, group=1)
async def check_filters(bot: Korone, message: Message):
    afilters = await get_all_filters(message.chat.id)

    if not afilters:
        return

    text = message.text

    if await filters.admin(bot, message):
        if text.startswith("/addfilter") or text.startswith("/delfilter"):
            return

    for rfilter in afilters:
        keyword = rfilter[1]
        if keyword.startswith("re:"):
            func = functools.partial(
                regex.search, keyword.replace("re:", "", 1), text, timeout=0.1
            )
        else:
            pattern = (
                r"( |^|[^\w])"
                + re.escape(keyword).replace("(+)", "(.*)")
                + r"( |$|[^\w])"
            )
            func = functools.partial(
                re.search,
                pattern,
                text,
                flags=re.IGNORECASE,
            )

        try:
            async with timeout(0.1):
                matched = await loop.run_in_executor(None, func)
        except (asyncio.TimeoutError, TimeoutError):
            continue

        user = await bot.get_users(message.from_user.id)
        if matched:
            if rfilter[4] == "text":
                await message.reply_text(
                    await vars_parser(
                        rfilter[2],
                        message,
                        user,
                    ),
                    parse_mode=ParseMode.MARKDOWN,
                )
            elif rfilter[4] == "photo":
                await message.reply_photo(
                    await vars_parser(
                        rfilter[3],
                        message,
                        user,
                    ),
                    parse_mode=ParseMode.MARKDOWN,
                )
            elif rfilter[4] == "document":
                await message.reply_document(
                    await vars_parser(
                        rfilter[3],
                        message,
                        user,
                    ),
                    parse_mode=ParseMode.MARKDOWN,
                )
            elif rfilter[4] == "video":
                await message.reply_video(
                    await vars_parser(
                        rfilter[3],
                        message,
                        user,
                    ),
                    parse_mode=ParseMode.MARKDOWN,
                )
            elif rfilter[4] == "audio":
                await message.reply_audio(
                    await vars_parser(
                        rfilter[3],
                        message,
                        user,
                    ),
                    parse_mode=ParseMode.MARKDOWN,
                )
            elif rfilter[4] == "animation":
                await message.reply_animation(
                    vars_parser(
                        rfilter[3],
                        message,
                        user,
                    ),
                    parse_mode=ParseMode.MARKDOWN,
                )
            elif rfilter[4] == "sticker":
                await message.reply_sticker(
                    await vars_parser(
                        rfilter[3],
                        message,
                        user,
                    ),
                    parse_mode=ParseMode.MARKDOWN,
                )


@Korone.on_message(filters.cmd("filters"))
@get_strings_dec("filters")
async def list_filters(bot: Korone, message: Message, strings):
    if message.chat.type == ChatType.PRIVATE:
        await message.reply_text(strings["only_for_groups"])
        return

    text = strings["list_filters"].format(chat_name=message.chat.title)

    filters = await get_all_filters(message.chat.id)
    if not filters:
        await message.reply_text(
            strings["no_filters_found"].format(chat_name=message.chat.title)
        )
        return

    for rfilter in filters:
        text += f"- <code>{rfilter[1]}</code>\n"

    await message.reply(text, disable_web_page_preview=True)


@Korone.on_message(filters.cmd("addfilter"))
@need_args_dec()
@get_strings_dec("filters")
async def new_filter(bot: Korone, message: Message, strings):
    if message.chat.type == ChatType.PRIVATE:
        await message.reply_text(strings["only_for_groups"])
        return

    if not await filters.admin(bot, message):
        await message.reply_text(
            strings["only_for_admins"].format(chat_name=message.chat.title)
        )
        return

    reply = message.reply_to_message
    args = message.text.markdown.split(maxsplit=1)
    extracted = split_quotes(args[1])
    if reply is None and len(extracted) < 2:
        await message.reply_text(strings["empty_filter"])
        return

    handler = extracted[0]
    filter_text = extracted[1] if len(extracted) > 1 else reply.text.markdown
    if handler.startswith("re:"):
        pattern = handler
        random_text_str = "".join(random.choice(printable) for i in range(50))
        try:
            regex.match(pattern, random_text_str, timeout=0.2)
        except TimeoutError:
            await message.reply(strings["regex_too_slow"])
            return
    else:
        handler = handler.lower()

    if reply and reply.photo:
        file_id = reply.photo.file_id
        raw_data = reply.caption.markdown if reply.caption else None
        filter_type = "photo"
    elif reply and reply.document:
        file_id = reply.document.file_id
        raw_data = reply.caption.markdown if reply.caption else None
        filter_type = "document"
    elif reply and reply.video:
        file_id = reply.video.file_id
        raw_data = reply.caption.markdown if reply.caption else None
        filter_type = "video"
    elif reply and reply.audio:
        file_id = reply.audio.file_id
        raw_data = reply.caption.markdown if reply.caption else None
        filter_type = "audio"
    elif reply and reply.animation:
        file_id = reply.animation.file_id
        raw_data = reply.caption.markdown if reply.caption else None
        filter_type = "animation"
    elif reply and reply.sticker:
        file_id = reply.sticker.file_id
        raw_data = filter_text if len(filter_text) > 1 else None
        filter_type = "sticker"
    else:
        file_id = None
        raw_data = filter_text
        filter_type = "text"

    check_filter = await check_for_filters(message.chat.id, handler)
    if check_filter:
        await update_filter(
            message.chat.id,
            handler,
            raw_data,
            file_id,
            filter_type,
        )
    else:
        await add_filter(
            message.chat.id,
            handler,
            raw_data,
            file_id,
            filter_type,
        )

    text = strings["filter_added"].format(
        filter=handler,
        chat_name=message.chat.title,
    )
    await message.reply_text(text)


@Korone.on_message(filters.cmd("delfilter"))
@need_args_dec()
@get_strings_dec("filters")
async def del_filter(bot: Korone, message: Message, strings):
    if message.chat.type == ChatType.PRIVATE:
        await message.reply_text(strings["only_for_groups"])
        return

    if not await filters.admin(bot, message):
        await message.reply_text(
            strings["only_for_admins"].format(chat_name=message.chat.title)
        )
        return

    args = message.text.markdown.split(maxsplit=1)
    handler = args[1]
    filter_exists = await check_for_filters(message.chat.id, handler)
    if not filter_exists:
        await message.reply_text(
            strings["no_such_filter"].format(chat_name=message.chat.title)
        )
        return

    await remove_filter(message.chat.id, handler)
    await message.reply_text(
        strings["filter_removed"].format(
            filter=handler,
            chat_name=message.chat.title,
        )
    )


__help__ = True

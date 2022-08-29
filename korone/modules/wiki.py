# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo M. <https://github.com/HitaloM>

import wikipedia
from pyrogram import filters
from pyrogram.helpers import ikb
from pyrogram.types import Message

from ..bot import Korone
from ..utils.aioify import run_async
from ..utils.languages import get_chat_lang, get_strings_dec
from ..utils.messages import get_args, need_args_dec


@Korone.on_message(filters.cmd("wiki"))
@need_args_dec()
@get_strings_dec("wiki")
async def wiki_search(bot: Korone, message: Message, strings):
    args = get_args(message)
    lang = await get_chat_lang(message.chat.id)
    await run_async(wikipedia.set_lang, lang)

    try:
        pagewiki = await run_async(wikipedia.page, args)
    except wikipedia.exceptions.PageError as e:
        await message.reply_text(strings["no_results"].format(error=e))
        return
    except wikipedia.exceptions.DisambiguationError as refer:
        refer = str(refer).split("\n")
        batas = min(len(refer), 6)
        text = "".join(
            refer[x] + "\n" if x == 0 else "- <code>" + refer[x] + "</code>\n"
            for x in range(batas)
        )
        await message.reply_text(text)
        return
    except IndexError:
        return

    title = pagewiki.title
    summary = pagewiki.summary[0:500]
    keyboard = ikb(
        [
            [
                (strings["read_more"], pagewiki.url, "url"),
            ],
        ],
    )

    await message.reply_text(
        f"<b>{title}</b>\n{summary}...",
        reply_markup=keyboard,
    )


__help__ = True

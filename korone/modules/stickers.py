# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

import os
import shutil
import tempfile

import httpx
from bs4 import BeautifulSoup as bs
from pyrogram import filters
from pyrogram.types import Message

from korone.bot import Korone
from korone.modules.utils.disable import disableable_dec
from korone.modules.utils.images import sticker_color_sync
from korone.modules.utils.languages import get_strings_dec
from korone.modules.utils.messages import get_args, need_args_dec
from korone.utils.aioify import run_async


@Korone.on_message(filters.cmd("getsticker") & filters.reply)
@disableable_dec("getsticker")
@get_strings_dec("stickers")
async def getsticker(bot: Korone, message: Message, strings):
    sticker = message.reply_to_message.sticker

    if not sticker:
        await message.reply_text(strings["not_sticker"])
        return

    if sticker.is_animated:
        await message.reply_text(strings["animated_unsupported"])
        return

    prefix = ".png" if not sticker.is_video else ".webm"
    with tempfile.TemporaryDirectory() as tempdir:
        path = os.path.join(tempdir, "getsticker")

    sticker_file = await bot.download_media(
        message=message.reply_to_message,
        file_name=f"{path}/{sticker.set_name}{prefix}",
    )

    await message.reply_to_message.reply_document(
        document=sticker_file,
        caption=(
            f"<b>Emoji:</b> {sticker.emoji}\n"
            f"<b>Sticker ID:</b> <code>{sticker.file_id}</code>"
        ),
    )
    shutil.rmtree(tempdir, ignore_errors=True)


@Korone.on_message(filters.cmd("stickers"))
@disableable_dec("stickers")
@need_args_dec()
@get_strings_dec("stickers")
async def sticker_search(bot: Korone, message: Message, strings):
    query = get_args(message)

    async with httpx.AsyncClient(http2=True) as client:
        r = await client.get(f"https://combot.org/telegram/stickers?page=1&q={query}")
        soup = bs(r.text, "lxml")
        main_div = soup.find("div", {"class": "sticker-packs-list"})
        titles = main_div.find_all("div", "sticker-pack__title")

        results = main_div.find_all("a", {"class": "sticker-pack__btn"})
        if not results:
            await message.reply_text(strings["no_results"].format(query=query))
            return

        text = strings["stickers_list"].format(query=query)
        for result, title in zip(results, titles):
            link = result["href"]
            text += f"\n - <a href='{link}'>{title.get_text()}</a>"

    await message.reply_text(text, disable_web_page_preview=True)


@Korone.on_message(filters.cmd("color"))
@need_args_dec()
@get_strings_dec("stickers")
async def color_sticker(bot: Korone, message: Message, strings):
    color = get_args(message)
    sticker = await run_async(sticker_color_sync, color)

    if sticker:
        await message.reply_sticker(sticker)
    else:
        await message.reply_text(
            strings["invalid_color"].format(color=color),
        )


__help__ = True

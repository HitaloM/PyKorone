# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo M. <https://github.com/HitaloM>

import shutil
import tempfile
from pathlib import Path

from pyrogram import filters
from pyrogram.types import Message

from ..bot import Korone
from ..utils.aioify import run_async
from ..utils.disable import disableable_dec
from ..utils.images import sticker_color_sync
from ..utils.languages import get_strings_dec
from ..utils.messages import get_args, need_args_dec


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
        path = Path(tempdir) / "getsticker"

    sticker_file = await bot.download_media(
        message=message.reply_to_message,
        file_name=f"{path}/{sticker.set_name}{prefix}",
    )

    await message.reply_to_message.reply_document(
        document=sticker_file,
        caption=(
            f"<b>Emoji:</b> {sticker.emoji}\n" f"<b>Sticker ID:</b> <code>{sticker.file_id}</code>"
        ),
    )
    shutil.rmtree(tempdir, ignore_errors=True)


@Korone.on_message(filters.cmd("color"))
@disableable_dec("color")
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

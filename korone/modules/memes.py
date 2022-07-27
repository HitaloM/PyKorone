# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

import httpx
from pyrogram import filters
from pyrogram.errors import BadRequest
from pyrogram.types import Message

from korone.bot import Korone
from korone.modules.utils.languages import get_strings_dec
from korone.modules.utils.messages import get_command


@Korone.on_message(filters.cmd(["neko", "waifu", "hug", "pat", "slap"]))
@get_strings_dec("memes")
async def neko_api(bot: Korone, message: Message, strings):
    command = get_command(message).lower()[1:].split("@")[0]
    async with httpx.AsyncClient(http2=True) as client:
        r = await client.get(f"https://nekos.life/api/v2/img/{command}")

    if r.status_code != 200:
        await message.reply_text(f"<b>Erro!</b>\n<code>{r.status}</code>")
        return

    image_url = (r.json())["url"]
    try:
        if message.reply_to_message:
            if command in ("neko", "waifu"):
                await message.reply_to_message.reply_photo(image_url)
            else:
                await message.reply_to_message.reply_document(image_url)
        elif command in ("neko", "waifu"):
            await message.reply_photo(image_url)
        else:
            await message.reply_document(image_url)
    except BadRequest as e:
        await message.reply_text(f"<b>Erro!</b>\n<code>{e}</code>")
        return


__help__ = True

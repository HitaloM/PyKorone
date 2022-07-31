# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

import httpx
from pyrogram import filters
from pyrogram.types import Message

from korone.bot import Korone
from korone.modules.utils.disable import disableable_dec
from korone.modules.utils.images import sticker_color_sync
from korone.modules.utils.languages import get_strings_dec
from korone.modules.utils.messages import get_args, need_args_dec
from korone.utils.aioify import run_async


@Korone.on_message(filters.cmd("cat"))
@disableable_dec("cat")
@get_strings_dec("misc")
async def cat_photo(bot: Korone, message: Message, strings):
    async with httpx.AsyncClient(http2=True) as client:
        r = await client.get("https://api.thecatapi.com/v1/images/search")

    if r.status_code != 200:
        await message.reply_text(strings["generic_error"])
        return

    cat = r.json()
    if cat[0]["url"].endswith(".gif"):
        await message.reply_animation(cat[0]["url"], caption="Meow!! (^つωฅ^)")
        return

    await message.reply_photo(cat[0]["url"], caption="Meow!! (^つωฅ^)")


@Korone.on_message(filters.cmd("dog"))
@disableable_dec("dog")
@get_strings_dec("misc")
async def dog_photo(bot: Korone, message: Message, strings):
    async with httpx.AsyncClient(http2=True) as client:
        r = await client.get("https://dog.ceo/api/breeds/image/random")

    if r.status_code != 200:
        await message.reply_text(strings["generic_error"])
        return

    dog = r.json()
    await message.reply_photo(dog["message"], caption="Woof!! U・ᴥ・U")


@Korone.on_message(filters.cmd("fox"))
@disableable_dec("fox")
@get_strings_dec("misc")
async def fox_photo(bot: Korone, message: Message, strings):
    async with httpx.AsyncClient(http2=True) as client:
        r = await client.get("https://randomfox.ca/floof/")

    if r.status_code != 200:
        await message.reply_text(strings["generic_error"])
        return

    fox = r.json()
    await message.reply_photo(fox["link"], caption="🦊")


@Korone.on_message(filters.cmd("panda"))
@disableable_dec("panda")
@get_strings_dec("misc")
async def panda_photo(bot: Korone, message: Message, strings):
    async with httpx.AsyncClient(http2=True) as client:
        r = await client.get("https://some-random-api.ml/img/panda")

    if r.status_code != 200:
        await message.reply_text(strings["generic_error"])
        return

    panda = r.json()
    await message.reply_photo(panda["link"], caption="🐼")


@Korone.on_message(filters.cmd("bird"))
@disableable_dec("bird")
@get_strings_dec("misc")
async def bird_photo(bot: Korone, message: Message, strings):
    async with httpx.AsyncClient(http2=True) as client:
        r = await client.get("https://shibe.online/api/birds")

    if r.status_code != 200:
        await message.reply_text(strings["generic_error"])
        return

    bird = r.json()
    await message.reply_photo(bird[0], caption="🐦")


@Korone.on_message(filters.cmd("redpanda"))
@disableable_dec("redpanda")
@get_strings_dec("misc")
async def rpanda_photo(bot: Korone, message: Message, strings):
    async with httpx.AsyncClient(http2=True) as client:
        r = await client.get("https://some-random-api.ml/img/red_panda")

    if r.status_code != 200:
        await message.reply_text(strings["generic_error"])
        return

    rpanda = r.json()
    await message.reply_photo(rpanda["link"], caption="🐼")


@Korone.on_message(filters.cmd("color"))
@need_args_dec()
@get_strings_dec("utilities")
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
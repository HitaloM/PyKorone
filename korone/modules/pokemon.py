# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo M. <https://github.com/HitaloM>

import httpx
from pyrogram import filters
from pyrogram.types import Message

from ..bot import Korone
from ..utils.aioify import run_async
from ..utils.disable import disableable_dec
from ..utils.images import pokemon_image_sync
from ..utils.languages import get_strings_dec
from ..utils.messages import get_args, get_command, need_args_dec


@Korone.on_message(filters.cmd(["pokemon", "backpokemon"]))
@disableable_dec("pokemon")
@need_args_dec()
@get_strings_dec("pokemon")
async def poke_image(bot: Korone, message: Message, strings):
    args = get_args(message).split(" ")
    view = get_command(message, pure=True)
    if view == "backpokemon":
        ptype = "back_"
    else:
        ptype = "front_"

    ptype += args[1] if len(args) > 1 else "default"
    async with httpx.AsyncClient(http2=True) as client:
        r = await client.get("https://pokeapi.co/api/v2/pokemon/" + args[0])

        if r.status_code != 200:
            await message.reply_text(strings["api_error"])
            return

        sprites = (r.json())["sprites"]
        if ptype not in sprites:
            await message.reply_text(strings["type_not_found"].format(type=args[1]))
            return

        sprite_url = sprites[ptype]
        if not sprite_url:
            await message.reply_text(strings["no_sprite"])
            return

        r = await client.get(sprite_url)
        if r.status_code != 200:
            await message.reply_text(strings["api_error"])
            return

    sprite_io = r.read()
    await message.reply_document(
        document=await run_async(pokemon_image_sync, sprite_io)
    )


@Korone.on_message(filters.cmd("pokeitem"))
@disableable_dec("pokeitem")
@need_args_dec()
@get_strings_dec("pokemon")
async def poke_item_image(bot: Korone, message: Message, strings):
    args = get_args(message)

    async with httpx.AsyncClient(http2=True) as client:
        r = await client.get(f"https://pokeapi.co/api/v2/item/{args}")

        if r.status_code != 200:
            await message.reply_text(strings["api_error"])
            return

        sprites = (r.json())["sprites"]
        sprite_url = sprites["default"]
        if not sprite_url:
            await message.reply_text(strings["unavailable_sprite"])
            return

        r = await client.get(sprite_url)
        if r.status_code != 200:
            await message.reply_text(strings["api_error"])
            return

    sprite_io = r.read()
    await message.reply_document(
        document=await run_async(pokemon_image_sync, sprite_io)
    )


__help__ = True

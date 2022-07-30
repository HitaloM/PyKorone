# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

import httpx
from pyrogram import filters
from pyrogram.types import Message

from korone.bot import Korone
from korone.modules.utils.disable import disableable_dec
from korone.modules.utils.images import pokemon_image_sync
from korone.modules.utils.languages import get_strings_dec
from korone.modules.utils.messages import get_args, get_command


@Korone.on_message(filters.cmd(["pokemon", "backpokemon"]))
@disableable_dec("pokemon")
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
    pk_img = pokemon_image_sync(sprite_io)
    await message.reply_document(pk_img)


@Korone.on_message(filters.cmd("pokeitem"))
@disableable_dec("pokeitem")
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
    pk_img = pokemon_image_sync(sprite_io)
    await message.reply_document(pk_img)


__help__ = True

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

import httpx
from pyrogram import filters
from pyrogram.types import Message

from korone.bot import Korone
from korone.modules.utils.images import pokemon_image_sync
from korone.modules.utils.messages import get_args, get_command


@Korone.on_message(filters.cmd(["pokemon", "backpokemon"]))
async def poke_image(bot: Korone, message: Message):
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
            await message.reply_text(f"<b>Error!</b> <code>{r.status_code}</code>")
            return

        sprites = (r.json())["sprites"]
        if ptype not in sprites:
            await message.reply_text(
                f"<code>Error! Tipo '{args[1]}' não encontrado!</code>"
            )
            return

        sprite_url = sprites[ptype]
        if not sprite_url:
            await message.reply_text("Esse Pokémon não tem um sprite disponível!")
            return

        r = await client.get(sprite_url)
        if r.status_code != 200:
            await message.reply_text(f"<b>Error!</b> <code>{r.status_code}</code>")
            return

    sprite_io = r.read()
    pk_img = pokemon_image_sync(sprite_io)
    await message.reply_document(pk_img)


@Korone.on_message(filters.cmd("pokeitem"))
async def poke_item_image(bot: Korone, message: Message):
    args = get_args(message)

    async with httpx.AsyncClient(http2=True) as client:
        r = await client.get(f"https://pokeapi.co/api/v2/item/{args}")

        if r.status_code != 200:
            await message.reply_text(f"<b>Error!</b> <code>{r.status_code}</code>")
            return

        sprites = (r.json())["sprites"]
        sprite_url = sprites["default"]
        if not sprite_url:
            await message.reply_text("Esse item Pokémon não tem um sprite disponível!")
            return

        r = await client.get(sprite_url)
        if r.status_code != 200:
            await message.reply_text(f"<b>Error!</b> <code>{r.status_code}</code>")
            return

    sprite_io = r.read()
    pk_img = pokemon_image_sync(sprite_io)
    await message.reply_document(pk_img)


__help__ = True

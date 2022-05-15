# SPDX-License-Identifier: GPL-3.0
# Copyright (c) 2020-2022 Amano Team

from typing import List

from pyrogram import filters
from pyrogram.types import Message

from korone.bot import Korone
from korone.handlers import COMMANDS_HELP
from korone.handlers.utils.image import pokemon_image_sync
from korone.utils import http

GROUP = "pokemon"

COMMANDS_HELP[GROUP] = {
    "name": "Pokémon",
    "text": "Um módulo para os treinadores Pokémon.",
    "commands": {},
    "help": True,
}


@Korone.on_message(
    filters.cmd(
        command="(?P<type>.*)pokemon (?P<search>.+)",
        action="Retorna o sprite do Pokémon específico, coloque 'back' antes de 'pokemon' para ver na visão traseira.",
        group=GROUP,
    )
)
async def poke_image(c: Korone, m: Message):
    type = m.matches[0]["type"]
    text = m.matches[0]["search"]
    args = text.split()

    types: List[str] = ["back", "front"]

    type = (type if type in types else "front") + "_"
    type += "_".join(args[1:]) if len(args) > 1 else "default"
    r = await http.get("https://pokeapi.co/api/v2/pokemon/" + args[0])
    if r.status_code == 200:
        sprites = (r.json())["sprites"]
        if type in sprites:
            sprite_url = sprites[type]
        else:
            await m.reply_text(
                f"<code>Error! Tipo \"{' '.join(args[1:])}\" não encontrado!</code>"
            )
            return
    else:
        await m.reply_text(f"<b>Error!</b> <code>{r.status_code}</code>")
        return

    if not sprite_url:
        await m.reply_text("Esse Pokémon não tem um sprite disponível!")
        return

    r = await http.get(sprite_url)
    if r.status_code == 200:
        sprite_io = r.read()
    else:
        await m.reply_text(f"<b>Error!</b> <code>{r.status_code}</code>")
        return

    pk_img = await pokemon_image_sync(sprite_io)
    await m.reply_document(pk_img)


@Korone.on_message(
    filters.cmd(
        command="pokeitem (?P<search>.+)",
        action="Retorna o sprite de um item Pokémon específico.",
        group=GROUP,
    )
)
async def poke_item_image(c: Korone, m: Message):
    text = m.matches[0]["search"]
    args = text.split()

    r = await http.get("https://pokeapi.co/api/v2/item/" + args[0])
    if r.status_code == 200:
        sprites = (r.json())["sprites"]
        sprite_url = sprites["default"]
    else:
        await m.reply_text(f"<b>Error!</b> <code>{r.status_code}</code>")
        return

    if not sprite_url:
        await m.reply_text("Esse item Pokémon não tem um sprite disponível!")
        return

    r = await http.get(sprite_url)
    if r.status_code == 200:
        sprite_io = r.read()
    else:
        await m.reply_text(f"<b>Error!</b> <code>{r.status_code}</code>")
        return

    pk_img = await pokemon_image_sync(sprite_io)
    await m.reply_document(pk_img)

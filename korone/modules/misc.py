# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo M. <https://github.com/HitaloM>

import asyncio
import contextlib
import html

import httpx
import regex
from async_timeout import timeout
from pyrogram import filters
from pyrogram.types import Message

from ..bot import Korone
from ..utils.disable import disableable_dec
from ..utils.languages import get_strings_dec
from ..utils.messages import get_args


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
    async with httpx.AsyncClient(http2=True, follow_redirects=True) as client:
        r = await client.get("https://some-random-api.ml/img/panda/")

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
    async with httpx.AsyncClient(http2=True, follow_redirects=True) as client:
        r = await client.get("https://some-random-api.ml/img/red_panda")

    if r.status_code != 200:
        await message.reply_text(strings["generic_error"])
        return

    rpanda = r.json()
    await message.reply_photo(rpanda["link"], caption="🐼")


@Korone.on_message(filters.cmd("mcserver"))
@disableable_dec("mcstatus")
@get_strings_dec("misc")
async def mcserver(bot: Korone, message: Message, strings):
    args = get_args(message)

    if not args:
        await message.reply_text(strings["mcstatus_no_args"])
        return

    reply = await message.reply_text(strings["mcstatus_fetching"])

    try:
        async with httpx.AsyncClient(http2=True) as client:
            r = await client.get(f"https://api.mcsrvstat.us/2/{args}")
    except httpx.TimeoutException:
        await reply.edit(strings["mcstatus_api_timeout"])
        return

    if r.status_code in [500, 504, 505]:
        await reply.edit(strings["mcstatus_api_unavailable"])
        return

    a = r.json()
    if a["online"]:
        text = "<b>Minecraft Server:</b>"
        text += f"\n<b>IP:</b> {a['hostname'] if 'hostname' in a else a['ip']}\
(<code>{a['ip']}</code>)"
        text += f"\n<b>Port:</b> <code>{a['port']}</code>"
        text += f"\n<b>Online:</b> <code>{a['online']}</code>"
        text += f"\n<b>Mods:</b> <code>{len(a['mods']['names']) if 'mods' in a else 'N/A'}</code>"
        text += f"\n<b>Players:</b> <code>{a['players']['online']}/{a['players']['max']}</code>"
        if "list" in a["players"]:
            text += "\n<b>Players list:</b> {}".format(
                ", ".join(
                    f"<a href='https://namemc.com/profile/{name}'>{name}</a>"
                    for name in a["players"]["list"]
                )
            )

        text += f"\n<b>Version:</b> <code>{a['version']}</code>"
        with contextlib.suppress(KeyError):
            text += f"\n<b>Software:</b> <code>{a['software']}</code>"
        text += f"\n<b>MOTD:</b> <i>{a['motd']['clean'][0]}</i>"

    elif not a["ip"] or a["ip"] == "127.0.0.1":
        await reply.edit(strings["mcstatus_invalid_server"])
        return

    else:
        text = (
            "<b>Minecraft Server</b>:"
            f"\n<b>IP:</b> {a['hostname'] if 'hostname' in a else a['ip']} \
(<code>{a['ip']}</code>)"
            f"\n<b>Port:</b> <code>{a['port']}</code>"
            f"\n<b>Online:</b> <code>{a['online']}</code>"
        )

    await reply.edit_text(text, disable_web_page_preview=True)


@Korone.on_message(filters.regex(r"^s/(.+)?/(.+)?(/.+)?") & filters.reply)
@disableable_dec("sed")
@get_strings_dec("misc")
async def sed(bot: Korone, message: Message, strings):
    exp = regex.split(r"(?<![^\\]\\)/", message.text)
    pattern = exp[1]
    replace_with = exp[2].replace(r"\/", "/")
    flags = exp[3] if len(exp) > 3 else ""

    count = 1
    rflags = 0

    if "g" in flags:
        count = 0
    if "i" in flags and "s" in flags:
        rflags = regex.I | regex.S
    elif "i" in flags:
        rflags = regex.I
    elif "s" in flags:
        rflags = regex.S

    text = message.reply_to_message.text or message.reply_to_message.caption

    if not text:
        return

    try:
        async with timeout(0.1):
            res = regex.sub(
                pattern,
                replace_with,
                text,
                count=count,
                flags=rflags,
            )
    except (asyncio.TimeoutError, TimeoutError):
        await message.reply_text(
            strings["regex_timeout"],
        )
        return
    except regex.error as e:
        await message.reply_text(
            strings["regex_error"].format(error=e),
        )
        return

    await message.reply_to_message.reply_text(html.escape(res))


__help__ = True

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

import base64
import binascii
import html

from asyncprawcore import exceptions as redex
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.helpers import ikb
from pyrogram.types import Message

from korone.bot import Korone
from korone.modules.utils.images import sticker_color_sync
from korone.modules.utils.languages import get_strings_dec
from korone.modules.utils.messages import get_args, need_args_dec
from korone.modules.utils.reddit import (
    REDDIT,
    bodyfetcherfallback,
    imagefetcherfallback,
    titlefetcherfallback,
)
from korone.utils.aioify import run_async


@Korone.on_message(filters.cmd("b64encode"))
@get_strings_dec("utilities")
async def b64e(bot: Korone, message: Message, strings):
    text = get_args(message)
    if not text:
        if message.reply_to_message:
            text = message.reply_to_message.text
        else:
            await message.reply_text(strings["need_text"])
            return

    b64 = base64.b64encode(text.encode("utf-8")).decode()
    await message.reply_text(f"<code>{b64}</code>")


@Korone.on_message(filters.cmd("b64decode"))
@get_strings_dec("utilities")
async def b64d(bot: Korone, message: Message, strings):
    text = get_args(message)
    if not text:
        if message.reply_to_message:
            text = message.reply_to_message.text
        else:
            await message.reply_text(strings["need_text"])
            return

    try:
        b64 = base64.b64decode(text).decode("utf-8", "replace")
    except binascii.Error as e:
        await message.reply_text(strings["invalid_b64"].format(error=e))
        return

    await message.reply_text(html.escape(b64))


@Korone.on_message(filters.cmd("redi"))
@need_args_dec()
@get_strings_dec("utilities")
async def reddit_image(bot: Korone, message: Message, strings):
    sub = get_args(message).split(" ")[0]
    image_url = False
    subreddit = await REDDIT.subreddit(sub)

    for _ in range(10):
        try:
            post = await subreddit.random() or await imagefetcherfallback(subreddit)

            if post.over_18:
                continue
        except redex.Forbidden:
            await message.reply_text(strings["reddit_private"].format(sub=sub))
            return
        except (redex.NotFound, KeyError):
            await message.reply_text(strings["reddit_not_found"].format(sub=sub))
            return
        except AttributeError:
            continue

        if post.url and post.url.endswith(
            (".mp4", ".jpg", ".jpeg", "jpe", ".png", ".gif")
        ):
            image_url = post.url
            title = post.title
            break

    if not image_url:
        await message.reply_text(strings["reddit_no_content"].format(sub=sub))
        return

    keyboard = ikb([[(f"r/{sub}", post.url, "url")]])

    try:
        if post.url.endswith(".mp4"):
            await message.reply_video(
                image_url,
                caption=title,
                reply_markup=keyboard,
            )
        if post.url.endswith((".jpg", ".jpeg", "jpe", ".png")):
            await message.reply_photo(
                image_url,
                caption=title,
                reply_markup=keyboard,
            )
        if post.url.endswith(".gif"):
            await message.reply_animation(
                image_url,
                caption=title,
                reply_markup=keyboard,
            )
    except BaseException:
        await message.reply_text(
            strings["reddit_download_error"].format(
                sub=sub, title=title, image_url=image_url
            )
        )


@Korone.on_message(filters.cmd("redt"))
@need_args_dec()
@get_strings_dec("utilities")
async def reddit_title(bot: Korone, message: Message, strings):
    sub = get_args(message).split(" ")[0]
    subreddit = await REDDIT.subreddit(sub)

    try:
        post = await subreddit.random() or await titlefetcherfallback(subreddit)
        title = post.title
    except redex.Forbidden:
        await message.reply_text(strings["reddit_private"].format(sub=sub))
        return
    except (redex.NotFound, KeyError):
        await message.reply_text(strings["reddit_not_found"].format(sub=sub))
        return
    except AttributeError:
        await message.reply_text(strings["reddit_no_content"].format(sub=sub))
        return

    keyboard = ikb([[(f"r/{sub}", post.url, "url")]])

    await message.reply_text(title, reply_markup=keyboard)


@Korone.on_message(filters.cmd("redb"))
@need_args_dec()
@get_strings_dec("utilities")
async def reddit_body(bot: Korone, message: Message, strings):
    sub = get_args(message).split(" ")[0]
    subreddit = await REDDIT.subreddit(sub)

    for _ in range(10):
        try:
            post = await subreddit.random() or await bodyfetcherfallback(subreddit)
            post.title
        except redex.Forbidden:
            await message.reply_text(strings["reddit_private"].format(sub=sub))
            return
        except (redex.NotFound, KeyError):
            await message.reply_text(strings["reddit_not_found"].format(sub=sub))
            return
        except AttributeError:
            continue

        body = None

        if post.selftext and post.permalink is not post.url:
            body = post.selftext
            title = post.title

        if not body:
            continue

        keyboard = ikb([[(f"r/{sub}", post.url, "url")]])

        await message.reply_text(
            f"<b>{title}</b>\n\n{html.escape(body)}",
            reply_markup=keyboard,
            parse_mode=ParseMode.DEFAULT,
        )
        return

    await message.reply_text(strings["reddit_no_content"].format(sub=sub))


@Korone.on_message(filters.cmd("color"))
@need_args_dec()
@get_strings_dec("utilities")
async def color_sticker(bot: Korone, message: Message, strings):
    color = get_args(message)

    if color_sticker:
        await message.reply_sticker(
            sticker=await run_async(
                sticker_color_sync,
                color,
            )
        )
    else:
        await message.reply_text(
            strings["invalid_color"].format(color=color),
        )


__help__ = True

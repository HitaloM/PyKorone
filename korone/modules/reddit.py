# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2020-2022 Hitalo <https://github.com/HitaloSama>

import html

from asyncprawcore import exceptions as redex
from pyrogram import filters
from pyrogram.enums import ParseMode
from pyrogram.helpers import ikb
from pyrogram.types import Message

from ..bot import Korone
from .utils.disable import disableable_dec
from .utils.languages import get_strings_dec
from .utils.messages import get_args, need_args_dec
from .utils.reddit import (
    REDDIT,
    bodyfetcherfallback,
    imagefetcherfallback,
    titlefetcherfallback,
)


@Korone.on_message(filters.cmd("redi"))
@disableable_dec("redi")
@need_args_dec()
@get_strings_dec("reddit")
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
@disableable_dec("redt")
@need_args_dec()
@get_strings_dec("reddit")
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
@disableable_dec("redb")
@need_args_dec()
@get_strings_dec("reddit")
async def reddit_body(bot: Korone, message: Message, strings):
    sub = get_args(message).split(" ")[0]
    subreddit = await REDDIT.subreddit(sub)

    for _ in range(10):
        try:
            post = await subreddit.random() or await bodyfetcherfallback(subreddit)
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


__help__ = True

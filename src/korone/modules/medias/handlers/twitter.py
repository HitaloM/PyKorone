# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import asyncio
import html
import re
from datetime import timedelta

import httpx
from hairydogm.chat_action import ChatActionSender
from hydrogram import Client
from hydrogram.enums import ChatAction
from hydrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    InputMediaVideo,
    Message,
)

from korone.decorators import router
from korone.filters import Regex
from korone.modules.medias.handlers.base_media_handler import BaseMediaHandler
from korone.modules.medias.utils.cache import MediaCache
from korone.modules.medias.utils.downloader import download_media
from korone.modules.medias.utils.files import resize_thumbnail
from korone.modules.medias.utils.twitter.api import TwitterError, fetch_tweet
from korone.modules.medias.utils.twitter.types import Media as TweetMedia
from korone.modules.medias.utils.twitter.types import MediaVariants as TweetMediaVariants
from korone.modules.medias.utils.twitter.types import Tweet
from korone.utils.i18n import gettext as _

URL_PATTERN = re.compile(
    r"""
    (?:(?:https?):\/\/)?
    (?:www\.)?
    (?:
        twitter |
        x |
        fxtwitter |
        vxtwitter |
        fix(?:upx|vx)
    )
    \.com
    /.+?/status/
    \d+
    """,
    re.IGNORECASE | re.VERBOSE,
)


@router.message(Regex(URL_PATTERN))
async def handle_twitter(client: Client, message: Message) -> None:
    if not message.text:
        return

    url_match = URL_PATTERN.search(message.text)
    if not url_match:
        return

    tweet = await fetch_tweet_data(url_match.group())
    if not tweet or not tweet.media or not tweet.media.all_medias:
        return

    tweet_text = format_tweet_text(tweet)
    cache = MediaCache(str(tweet.url))
    cached_data = await cache.get()

    if len(tweet.media.all_medias) > 1:
        tweet_text += f"\n<a href='{tweet.url!s}'>{_('Open in Twitter')}</a>"
        await process_multiple_media(client, message, tweet, tweet_text, cached_data)
    else:
        sent_message = await send_media(
            client, message, tweet.media.all_medias[0], tweet_text, tweet, cached_data
        )
        if sent_message:
            await cache.set(sent_message, int(timedelta(weeks=1).total_seconds()))


async def fetch_tweet_data(url: str) -> Tweet | None:
    try:
        return await fetch_tweet(url)
    except TwitterError:
        return None


def format_tweet_text(tweet: Tweet) -> str:
    text = f"<b>{tweet.author.name} (<code>@{tweet.author.screen_name}</code>):</b>\n"
    if tweet.text:
        text += html.escape(f"\n{tweet.text[:900]}{'...' if len(tweet.text) > 900 else ''}\n")
    if tweet.source:
        text += _("\n<b>Sent from:</b> <i>{source}</i>").format(source=tweet.source)
    return text


async def process_multiple_media(
    client: Client,
    message: Message,
    tweet: Tweet,
    text: str,
    cached_data: list[InputMediaPhoto | InputMediaVideo] | None,
) -> None:
    cache = MediaCache(str(tweet.url))

    if not tweet.media or not tweet.media.all_medias:
        return

    media_list = cached_data or await prepare_media_list(tweet.media.all_medias, text)

    if not media_list:
        return

    media_list[-1].caption = text

    async with ChatActionSender(
        client=client, chat_id=message.chat.id, action=ChatAction.UPLOAD_PHOTO
    ):
        sent_message = await message.reply_media_group(media=media_list)

    if sent_message:
        await cache.set(sent_message, int(timedelta(weeks=1).total_seconds()))


async def prepare_media_list(
    media_list: list[TweetMedia], text: str
) -> list[InputMediaPhoto | InputMediaVideo]:
    media_tasks = [prepare_media(media) for media in media_list]
    return [media for media in await asyncio.gather(*media_tasks) if media]


async def prepare_media(media: TweetMedia) -> InputMediaPhoto | InputMediaVideo | None:
    optimal_media = get_optimal_variant(media) or media
    try:
        media_file = await download_media(str(optimal_media.url))
        if not media_file:
            return None
    except httpx.HTTPStatusError as e:
        media_file = handle_http_error(e)
        return InputMediaPhoto(media_file) if media_file else None

    if media.media_type == "photo":
        return InputMediaPhoto(media_file)

    if media.media_type in {"video", "gif"}:
        thumb_file = (
            await download_media(str(media.thumbnail_url)) if media.thumbnail_url else None
        )
        if thumb_file:
            await asyncio.to_thread(resize_thumbnail, thumb_file)
        return InputMediaVideo(
            media=media_file,
            duration=media.duration,
            width=media.width,
            height=media.height,
            thumb=thumb_file,
        )

    return None


def get_optimal_variant(media: TweetMedia) -> TweetMediaVariants | None:
    return (
        max(media.variants, key=lambda variant: variant.bitrate or 0) if media.variants else None
    )


def handle_http_error(e: httpx.HTTPStatusError) -> str | None:
    if e.response.status_code == 403:
        error_response = e.response.json().get("error_response")
        if error_response == "Dmcaed" or e.response.status_code == 307:
            return "https://pbs.twimg.com/static/dmca/dmca-med.jpg"
    return None


async def send_media(
    client: Client,
    message: Message,
    media: TweetMedia,
    text: str,
    tweet: Tweet,
    cache_data: list[InputMediaPhoto | InputMediaVideo] | None,
) -> Message | None:
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(_("Open in Twitter"), url=str(tweet.url))]
    ])
    media_file = cache_data[0] if cache_data else await prepare_media(media)

    if not media_file:
        return None

    # Truncate text to fit Telegram's character limit
    text = BaseMediaHandler.truncate_caption(text)

    action = (
        ChatAction.UPLOAD_PHOTO
        if isinstance(media_file, InputMediaPhoto)
        else ChatAction.UPLOAD_VIDEO
    )
    async with ChatActionSender(client=client, chat_id=message.chat.id, action=action):
        if isinstance(media_file, InputMediaPhoto):
            return await client.send_photo(
                chat_id=message.chat.id,
                photo=media_file.media,
                caption=text,
                reply_markup=keyboard,
                reply_to_message_id=message.id,
            )
        return await client.send_video(
            chat_id=message.chat.id,
            video=media_file.media,
            caption=text,
            reply_markup=keyboard,
            no_sound=True,
            duration=media_file.duration,
            width=media_file.width,
            height=media_file.height,
            thumb=media_file.thumb,
            reply_to_message_id=message.id,
        )

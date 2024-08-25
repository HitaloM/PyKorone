# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio
import re
from datetime import timedelta

import httpx
from hairydogm.chat_action import ChatActionSender
from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.enums import ChatAction
from hydrogram.types import InputMediaPhoto, InputMediaVideo, Message

from korone.decorators import router
from korone.filters import Regex
from korone.modules.medias.utils.cache import MediaCache
from korone.modules.medias.utils.files import resize_thumbnail, url_to_bytes_io
from korone.modules.medias.utils.twitter import (
    Tweet,
    TweetMedia,
    TweetMediaVariants,
    TwitterError,
    fetch_tweet,
)
from korone.utils.i18n import gettext as _

URL_PATTERN = re.compile(r"(?:(?:http|https):\/\/)?(?:www.)?(twitter\.com|x\.com)/.+?/status/\d+")


@router.message(Regex(URL_PATTERN))
async def handle_twitter(client: Client, message: Message) -> None:
    url_match = URL_PATTERN.search(message.text)
    if not url_match:
        return

    try:
        tweet = await fetch_tweet(url_match.group())
    except TwitterError:
        return

    if not tweet or not tweet.media or not tweet.media.all_medias:
        return

    tweet_text = format_tweet_text(tweet)
    if len(tweet.media.all_medias) > 1:
        tweet_text += f"\n<a href='{tweet.url!s}'>{_("Open in Twitter")}</a>"
        await process_multiple_media(client, message, tweet, tweet_text)
        return

    cache = MediaCache(str(tweet.url))
    cached_data = await cache.get()
    sent_message = await send_media(
        client, message, tweet.media.all_medias[0], tweet_text, tweet, cached_data
    )
    if sent_message:
        await cache.set(sent_message, int(timedelta(weeks=1).total_seconds()))


def get_optimal_variant(media: TweetMedia) -> TweetMediaVariants | None:
    return (
        max(media.variants, key=lambda variant: variant.bitrate or 0) if media.variants else None
    )


def build_media_list(media_cache: dict, text: str) -> list[InputMediaPhoto | InputMediaVideo]:
    media_list = [InputMediaPhoto(media["file"]) for media in media_cache.get("photo", [])] + [
        InputMediaVideo(
            media=media["file"],
            duration=media["duration"],
            width=media["width"],
            height=media["height"],
            thumb=media["thumbnail"],
        )
        for media in media_cache.get("video", [])
    ]
    if media_list:
        media_list[-1].caption = text
    return media_list


def handle_http_error(e: httpx.HTTPStatusError) -> str | None:
    error_response = None
    if e.response.status_code == 403:
        error_response = e.response.json().get("error_response")
    if error_response == "Dmcaed" or e.response.status_code == 307:
        return "https://pbs.twimg.com/static/dmca/dmca-med.jpg"
    return None


async def prepare_media(media: TweetMedia) -> InputMediaPhoto | InputMediaVideo | None:
    optimal_media = get_optimal_variant(media) or media
    try:
        media_file = await url_to_bytes_io(optimal_media.url, video=media.media_type != "photo")
    except httpx.HTTPStatusError as e:
        media_file = handle_http_error(e)
        if media_file:
            return InputMediaPhoto(media_file)
        return None

    if media.media_type == "photo":
        return InputMediaPhoto(media_file)

    if media.media_type in {"video", "gif"}:
        thumb_file = (
            await url_to_bytes_io(media.thumbnail_url, video=True) if media.thumbnail_url else None
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


async def process_multiple_media(
    client: Client, message: Message, tweet: Tweet, text: str
) -> None:
    cache = MediaCache(str(tweet.url))
    media_cache = await cache.get()
    media_list = build_media_list(media_cache, text) if media_cache else []

    if not media_list and tweet.media and tweet.media.all_medias:
        media_tasks = [prepare_media(media) for media in tweet.media.all_medias]
        media_list = [media for media in await asyncio.gather(*media_tasks) if media]
        media_list[-1].caption = text

    async with ChatActionSender(
        client=client, chat_id=message.chat.id, action=ChatAction.UPLOAD_PHOTO
    ):
        sent_message = await message.reply_media_group(media=media_list)

    if sent_message:
        await cache.set(sent_message, int(timedelta(weeks=1).total_seconds()))


async def send_media(
    client: Client,
    message: Message,
    media: TweetMedia,
    text: str,
    tweet: Tweet,
    cache_data: dict | None,
) -> Message | None:
    keyboard = InlineKeyboardBuilder().button(text=_("Open in Twitter"), url=str(tweet.url))
    media_file, thumb_file, duration, width, height = (
        None,
        None,
        media.duration,
        media.width,
        media.height,
    )

    if cache_data:
        if media.media_type == "photo" and cache_data.get("photo"):
            media_file = cache_data["photo"][0].get(
                "file", await url_to_bytes_io(media.url, video=False)
            )
        elif media.media_type in {"video", "gif"} and cache_data.get("video"):
            video_data = cache_data["video"][0]
            media_file = video_data.get("file", await url_to_bytes_io(media.url, video=True))
            duration = video_data.get("duration", duration)
            width = video_data.get("width", media.width)
            height = video_data.get("height", media.height)
            thumb_file = video_data.get("thumbnail", media.thumbnail_url)

    if not media_file:
        try:
            media_file = await url_to_bytes_io(media.url, video=media.media_type != "photo")
            if media.media_type in {"video", "gif"} and media.thumbnail_url:
                thumb_file = await url_to_bytes_io(media.thumbnail_url, video=True)
                await asyncio.to_thread(resize_thumbnail, thumb_file)
        except httpx.HTTPStatusError as e:
            media_file = handle_http_error(e)
            if not media_file:
                return None
            media.media_type = "photo"

    if not media_file:
        return None

    action = ChatAction.UPLOAD_PHOTO if media.media_type == "photo" else ChatAction.UPLOAD_VIDEO
    async with ChatActionSender(client=client, chat_id=message.chat.id, action=action):
        if media.media_type == "photo":
            return await client.send_photo(
                chat_id=message.chat.id,
                photo=media_file,
                caption=text,
                reply_markup=keyboard.as_markup(),
                reply_to_message_id=message.id,
            )

        return await client.send_video(
            chat_id=message.chat.id,
            video=media_file,
            caption=text,
            reply_markup=keyboard.as_markup(),
            no_sound=True,
            duration=duration,
            width=width,
            height=height,
            thumb=thumb_file,
            reply_to_message_id=message.id,
        )


def format_tweet_text(tweet: Tweet) -> str:
    text = f"<b>{tweet.author.name} (<code>@{tweet.author.screen_name}</code>):</b>\n"
    if tweet.text:
        text += f"\n{tweet.text[:900]}{"..." if len(tweet.text) > 900 else ""}\n"
    if tweet.source:
        text += _("\n<b>Sent from:</b> <i>{source}</i>").format(source=tweet.source)
    return text

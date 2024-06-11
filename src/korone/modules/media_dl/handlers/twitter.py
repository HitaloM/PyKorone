# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio
import re
from datetime import timedelta
from functools import partial

from hairydogm.chat_action import ChatActionSender
from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client, filters
from hydrogram.enums import ChatAction
from hydrogram.types import InputMediaPhoto, InputMediaVideo, Message

from korone.decorators import router
from korone.handlers.abstract import MessageHandler
from korone.modules.media_dl.utils.cache import MediaCache
from korone.modules.media_dl.utils.twitter import (
    TweetData,
    TweetMedia,
    TwitterAPI,
    TwitterError,
    delete_files,
    get_best_variant,
    process_video_media,
)
from korone.utils.i18n import gettext as _

URL_PATTERN = re.compile(r"(?:(?:http|https):\/\/)?(?:www.)?(twitter\.com|x\.com)/.+?/status/\d+")


class TwitterMessageHandler(MessageHandler):
    @staticmethod
    def create_media_list(media_cache: dict, text: str) -> list[InputMediaPhoto | InputMediaVideo]:
        media_list = []

        media_list.extend(
            [InputMediaPhoto(media["file"]) for media in media_cache.get("photo", [])]
            + [
                InputMediaVideo(
                    media=media["file"],
                    duration=media["duration"],
                    width=media["width"],
                    height=media["height"],
                    thumb=media["thumbnail"],
                )
                for media in media_cache.get("video", [])
            ]
        )

        if media_list:
            media_list[-1].caption = text

        return media_list

    @staticmethod
    async def process_media(
        media: TweetMedia, files_to_delete: list
    ) -> InputMediaPhoto | InputMediaVideo | None:
        if media.type == "photo":
            return InputMediaPhoto(media.binary_io)

        if media.type in {"video", "gif"}:
            variant = get_best_variant(media) or media
            media_file = await process_video_media(variant)
            duration = int(timedelta(milliseconds=media.duration).total_seconds())
            files_to_delete.append(media_file)

            return InputMediaVideo(
                media=media_file,
                duration=duration,
                width=media.width,
                height=media.height,
                thumb=media.thumbnail_io,
            )
        return None

    async def handle_multiple_media(self, message: Message, tweet: TweetData, text: str) -> None:
        cache = MediaCache(tweet.url)
        media_cache = await cache.get()

        if media_cache:
            media_list = self.create_media_list(media_cache, text)
            await message.reply_media_group(media=media_list)
            return

        files_to_delete = []
        process_media_partial = partial(self.process_media, files_to_delete=files_to_delete)

        media_tasks = [process_media_partial(media) for media in tweet.media]

        media_list = []
        for coro in asyncio.as_completed(media_tasks):
            media = await coro
            if media:
                media_list.append(media)

        media_list[-1].caption = text
        sent_message = await message.reply_media_group(media=media_list)

        if files_to_delete:
            await delete_files(files_to_delete)

        if sent_message:
            cache_ttl = int(timedelta(weeks=1).total_seconds())
            await cache.set(sent_message, cache_ttl)

    @staticmethod
    async def send_media(  # noqa: PLR0917
        client: Client,
        message: Message,
        media: TweetMedia,
        text: str,
        tweet: TweetData,
        cache_data: dict | None,
    ) -> Message | None:
        keyboard = InlineKeyboardBuilder().button(text=_("Open in Twitter"), url=tweet.url)

        media_file = media.binary_io
        duration = (
            int(timedelta(milliseconds=media.duration).total_seconds()) if media.duration else 0
        )
        width = media.width
        height = media.height
        thumb = media.thumbnail_io

        if cache_data:
            if media.type == "photo" and cache_data.get("photo"):
                media_file = cache_data["photo"][0].get("file", media_file)
            elif media.type in {"video", "gif"} and cache_data.get("video"):
                video_data = cache_data["video"][0]
                media_file = video_data.get("file", media_file)
                duration = video_data.get("duration", duration)
                width = video_data.get("width", width)
                height = video_data.get("height", height)
                thumb = video_data.get("thumbnail", thumb)

        try:
            if media.type == "photo":
                if not media_file:
                    await message.reply_text(_("Failed to send media!"))
                    return None

                return await client.send_photo(
                    chat_id=message.chat.id,
                    photo=media_file,
                    caption=text,
                    reply_markup=keyboard.as_markup(),
                    reply_to_message_id=message.id,
                )
            if media.type in {"video", "gif"}:
                if not media_file:
                    await message.reply_text(_("Failed to send media!"))
                    return None

                return await client.send_video(
                    chat_id=message.chat.id,
                    video=media_file,
                    caption=text,
                    reply_markup=keyboard.as_markup(),
                    duration=duration,
                    width=width,
                    height=height,
                    thumb=thumb,
                    reply_to_message_id=message.id,
                )
        except Exception as e:
            await message.reply_text(_("Failed to send media: {error}").format(error=e))
        return None

    @staticmethod
    def format_tweet_text(tweet: TweetData) -> str:
        text = (
            f"<b>{tweet.author.name} (<code>@{tweet.author.screen_name}</code>)"
            f"{":" if tweet.text else ""}</b>\n"
        )
        if tweet.text:
            text += f"\n{tweet.text[:900]}{"..." if len(tweet.text) > 900 else ""}\n"

        if tweet.source:
            text += _("\n<b>Sent from:</b> <i>{source}</i>").format(source=tweet.source)
        return text

    @router.message(filters.regex(URL_PATTERN))
    async def handle(self, client: Client, message: Message) -> None:
        url_match = URL_PATTERN.search(message.text)
        if not url_match:
            return

        try:
            api = TwitterAPI(url_match.group())
            await api.fetch_and_parse()
            tweet = api.tweet
        except TwitterError:
            await message.reply_text(
                _(
                    "Failed to scan your link! This may be due to an incorrect link, "
                    "private/suspended account, deleted tweet, or recent changes to "
                    "Twitter's API."
                )
            )
            return

        if not tweet:
            await message.reply_text(_("I couldn't find any tweet data!"))
            return

        if not tweet.media:
            await message.reply_text(_("No media found in this tweet!"))
            return

        text = self.format_tweet_text(tweet)
        async with ChatActionSender(
            client=client, chat_id=message.chat.id, action=ChatAction.UPLOAD_DOCUMENT
        ):
            if len(tweet.media) > 1:
                text += f"\n<a href='{tweet.url}'>{_("Open in Twitter")}</a>"
                await self.handle_multiple_media(message, tweet, text)
                return

            cache = MediaCache(tweet.url)
            cache_data = await cache.get()
            try:
                sent_message = await self.send_media(
                    client, message, tweet.media[0], text, tweet, cache_data
                )
            except Exception as e:
                await message.reply_text(_("Failed to send media: {error}").format(error=e))
            else:
                cache_ttl = int(timedelta(weeks=1).total_seconds())
                await cache.set(sent_message, cache_ttl) if sent_message else None

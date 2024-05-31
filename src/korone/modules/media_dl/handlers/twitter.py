# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio
import re
from datetime import timedelta
from functools import partial

from hairydogm.chat_action import ChatActionSender
from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.enums import ChatAction
from hydrogram.types import InputMediaPhoto, InputMediaVideo, Message
from magic_filter import F

from korone.decorators import router
from korone.handlers import MessageHandler
from korone.modules.media_dl.utils.twitter import (
    TweetData,
    TwitterAPI,
    TwitterCache,
    TwitterError,
    TwitterMediaHandler,
)
from korone.utils.i18n import gettext as _

URL_PATTERN = re.compile(r"(?:(?:http|https):\/\/)?(?:www.)?(twitter\.com|x\.com)/.+?/status/\d+")


class TwitterMessageHandler(MessageHandler):
    __slots__ = ("media_handler",)

    def __init__(self) -> None:
        self.media_handler = TwitterMediaHandler()

    @staticmethod
    def create_media_list(media_cache: dict, text: str) -> list[InputMediaPhoto | InputMediaVideo]:
        media_list = [
            InputMediaPhoto(media["photo"])
            if "photo" in media
            else InputMediaVideo(
                media=media["video"]["file"],
                duration=media["video"]["duration"],
                width=media["video"]["width"],
                height=media["video"]["height"],
                thumb=media["video"]["thumbnail"],
            )
            for media in media_cache.values()
        ]
        media_list[-1].caption = text
        return media_list

    async def process_media(
        self, media, files_to_delete: list
    ) -> InputMediaPhoto | InputMediaVideo | None:
        if media.type == "photo":
            return InputMediaPhoto(media.binary_io)

        if media.type in {"video", "gif"}:
            variant = await self.media_handler.get_best_variant(media) or media
            media_file = await self.media_handler.process_video_media(variant)
            files_to_delete.append(media_file)
            thumbnail_io = await self.media_handler.api._url_to_binary_io(media.thumbnail_url)

            return InputMediaVideo(
                media=media_file,
                duration=int(timedelta(milliseconds=media.duration).total_seconds()),
                width=media.width,
                height=media.height,
                thumb=thumbnail_io,
            )
        return None

    async def handle_multiple_media(self, message: Message, tweet: TweetData, text: str) -> None:
        cache = TwitterCache(tweet)
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
            await self.media_handler.files_utils.delete_files(files_to_delete)

        if sent_message:
            cache_ttl = int(timedelta(weeks=1).total_seconds())
            await cache.set(sent_message, cache_ttl)

    async def send_media(  # noqa: PLR0917
        self,
        client: Client,
        message: Message,
        media,
        text: str,
        tweet: TweetData,
        cache_data: dict | None,
    ) -> Message | None:
        keyboard = InlineKeyboardBuilder().button(text=_("Open in Twitter"), url=tweet.url)
        media_file = media.binary_io

        try:
            if media.type == "photo":
                media_file = cache_data["photo"]["file"] if cache_data else media_file
                return await client.send_photo(
                    chat_id=message.chat.id,
                    photo=media_file,
                    caption=text,
                    reply_markup=keyboard.as_markup(),
                    reply_to_message_id=message.id,
                )

            if media.type in {"video", "gif"}:
                if not cache_data:
                    thumbnail_io = await self.media_handler.api._url_to_binary_io(
                        media.thumbnail_url
                    )
                    media_file = (
                        await self.media_handler.get_best_variant(media) or media
                    ).binary_io
                else:
                    media_file = cache_data["video"]["file"]

                if not media_file:
                    await message.reply_text(_("Failed to send media!"))
                    return None

                return await client.send_video(
                    chat_id=message.chat.id,
                    video=media_file,
                    caption=text,
                    reply_markup=keyboard.as_markup(),
                    duration=cache_data.get("duration", 0)
                    if cache_data
                    else int(timedelta(milliseconds=media.duration).total_seconds()),
                    width=cache_data.get("width", 0) if cache_data else media.width,
                    height=cache_data.get("height", 0) if cache_data else media.height,
                    thumb=cache_data.get("thumbnail") if cache_data else thumbnail_io,
                    reply_to_message_id=message.id,
                )
        except Exception as e:
            await message.reply_text(_("Failed to send media: {error}").format(error=e))
        return None

    @staticmethod
    def format_tweet_text(tweet: TweetData) -> str:
        text = f"<b>{tweet.author.name} (<code>@{tweet.author.screen_name}</code>):</b>\n\n"
        if tweet.text:
            text += f"{tweet.text[:900]}{"..." if len(tweet.text) > 900 else ""}"

        if tweet.source:
            text += _("\n\n<b>Sent from:</b> <i>{source}</i>").format(source=tweet.source)
        return text

    @router.message(F.text.regexp(URL_PATTERN, search=True))
    async def handle(self, client: Client, message: Message) -> None:
        url_match = URL_PATTERN.search(message.text)
        if not url_match:
            return

        try:
            api = TwitterAPI()
            await api.fetch(url_match.group())
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

        if not tweet.media:
            await message.reply_text(_("No media found in this tweet!"))
            return

        text = self.format_tweet_text(tweet)
        async with ChatActionSender(
            client=client, chat_id=message.chat.id, action=ChatAction.UPLOAD_DOCUMENT
        ):
            if len(tweet.media) > 1:
                text += f"\n<a href='{tweet.url}'>Open in Twitter</a>"
                await self.handle_multiple_media(message, tweet, text)
                return

            cache = TwitterCache(tweet)
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

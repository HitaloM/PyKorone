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

from korone.decorators import router
from korone.filters import Regex
from korone.handlers.abstract import MessageHandler
from korone.modules.medias.utils.cache import MediaCache
from korone.modules.medias.utils.files import resize_thumbnail, url_to_bytes_io
from korone.modules.medias.utils.twitter import (
    Tweet,
    TweetMedia,
    TweetMediaVariants,
    TwitterAPI,
    TwitterError,
)
from korone.utils.i18n import gettext as _

URL_PATTERN = re.compile(r"(?:(?:http|https):\/\/)?(?:www.)?(twitter\.com|x\.com)/.+?/status/\d+")


class TwitterMessageHandler(MessageHandler):
    @staticmethod
    def get_best_variant(media: TweetMedia) -> TweetMediaVariants | None:
        if not media.variants:
            return None

        return max(media.variants, key=lambda variant: variant.bitrate or 0)

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

    async def process_media(self, media: TweetMedia) -> InputMediaPhoto | InputMediaVideo | None:
        if media.media_type == "photo":
            media_file = await url_to_bytes_io(media.url, video=False)
            return InputMediaPhoto(media_file)

        if media.media_type in {"video", "gif"}:
            best_media = self.get_best_variant(media) or media
            media_file = await url_to_bytes_io(best_media.url, video=True)
            thumb_file = None
            if media.thumbnail_url:
                thumb_file = await url_to_bytes_io(media.thumbnail_url, video=True)
                await asyncio.to_thread(resize_thumbnail, thumb_file)
            duration = int(timedelta(milliseconds=media.duration).total_seconds())

            return InputMediaVideo(
                media=media_file,
                duration=duration,
                width=media.width,
                height=media.height,
                thumb=thumb_file,
            )
        return None

    async def handle_multiple_media(
        self, client: Client, message: Message, tweet: Tweet, text: str
    ) -> None:
        cache = MediaCache(str(tweet.url))
        media_cache = await cache.get()

        if media_cache:
            media_list = self.create_media_list(media_cache, text)
            async with ChatActionSender(
                client=client, chat_id=message.chat.id, action=ChatAction.UPLOAD_PHOTO
            ):
                await message.reply_media_group(media=media_list)
            return

        process_media_partial = partial(self.process_media)

        media_tasks = [process_media_partial(media) for media in tweet.media.all_medias]

        media_list = []
        for coro in asyncio.as_completed(media_tasks):
            media = await coro
            if media:
                media_list.append(media)

        media_list[-1].caption = text
        async with ChatActionSender(
            client=client, chat_id=message.chat.id, action=ChatAction.UPLOAD_PHOTO
        ):
            sent_message = await message.reply_media_group(media=media_list)

        if sent_message:
            cache_ttl = int(timedelta(weeks=1).total_seconds())
            await cache.set(sent_message, cache_ttl)

    @staticmethod
    async def send_media(  # noqa: PLR0917
        client: Client,
        message: Message,
        media: TweetMedia,
        text: str,
        tweet: Tweet,
        cache_data: dict | None,
    ) -> Message | None:
        keyboard = InlineKeyboardBuilder().button(text=_("Open in Twitter"), url=str(tweet.url))

        duration = (
            int(timedelta(milliseconds=media.duration).total_seconds()) if media.duration else 0
        )
        width = media.width
        height = media.height
        thumb = media.thumbnail_url

        if cache_data:
            if media.media_type == "photo" and cache_data.get("photo"):
                media_file = cache_data["photo"][0].get(
                    "file", await url_to_bytes_io(media.url, video=False)
                )
            elif media.media_type in {"video", "gif"} and cache_data.get("video"):
                video_data = cache_data["video"][0]
                media_file = video_data.get("file", await url_to_bytes_io(media.url, video=True))
                duration = video_data.get("duration", duration)
                width = video_data.get("width", width)
                height = video_data.get("height", height)
                thumb = video_data.get("thumbnail", thumb)

        try:
            if media.media_type == "photo":
                media_file = await url_to_bytes_io(media.url, video=False)

                if not media_file:
                    await message.reply(_("Failed to send media!"))
                    return None

                async with ChatActionSender(
                    client=client, chat_id=message.chat.id, action=ChatAction.UPLOAD_PHOTO
                ):
                    return await client.send_photo(
                        chat_id=message.chat.id,
                        photo=media_file,
                        caption=text,
                        reply_markup=keyboard.as_markup(),
                        reply_to_message_id=message.id,
                    )
            if media.media_type in {"video", "gif"}:
                media_file = await url_to_bytes_io(media.url, video=True)
                if not media_file:
                    await message.reply(_("Failed to send media!"))
                    return None

                thumb_file = None
                if media.thumbnail_url:
                    thumb_file = await url_to_bytes_io(media.thumbnail_url, video=True)
                    await asyncio.to_thread(resize_thumbnail, thumb_file)

                async with ChatActionSender(
                    client=client, chat_id=message.chat.id, action=ChatAction.UPLOAD_VIDEO
                ):
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
        except Exception:
            raise
        return None

    @staticmethod
    def format_tweet_text(tweet: Tweet) -> str:
        text = (
            f"<b>{tweet.author.name} (<code>@{tweet.author.screen_name}</code>)"
            f"{":" if tweet.text else ""}</b>\n"
        )
        if tweet.text:
            text += f"\n{tweet.text[:900]}{"..." if len(tweet.text) > 900 else ""}\n"

        if tweet.source:
            text += _("\n<b>Sent from:</b> <i>{source}</i>").format(source=tweet.source)
        return text

    @router.message(Regex(URL_PATTERN))
    async def handle(self, client: Client, message: Message) -> None:
        url_match = URL_PATTERN.search(message.text)
        if not url_match:
            return

        api = TwitterAPI(url_match.group())

        try:
            tweet = await api.fetch()
        except TwitterError:
            return

        if not tweet:
            return

        if not tweet.media:
            return

        text = self.format_tweet_text(tweet)

        if len(tweet.media.all_medias) > 1:
            text += f"\n<a href='{tweet.url!s}'>{_("Open in Twitter")}</a>"
            await self.handle_multiple_media(client, message, tweet, text)
            return

        cache = MediaCache(str(tweet.url))
        cache_data = await cache.get()
        try:
            sent_message = await self.send_media(
                client, message, tweet.media.all_medias[0], text, tweet, cache_data
            )
        except Exception:
            raise
        else:
            cache_ttl = int(timedelta(weeks=1).total_seconds())
            await cache.set(sent_message, cache_ttl) if sent_message else None

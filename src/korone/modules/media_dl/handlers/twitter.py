# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import re
from datetime import timedelta

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
    TweetMedia,
    TweetMediaVariants,
    TwitterAPI,
    TwitterError,
)
from korone.utils.i18n import gettext as _

URL_PATTERN = re.compile(r"(?:(?:http|https):\/\/)?(?:www.)?(twitter\.com|x\.com)/.+?/status/\d+")


class TwitterHandler(MessageHandler):
    @staticmethod
    async def get_best_variant(media: TweetMedia) -> TweetMediaVariants | None:
        if not media.variants:
            return None

        return max(media.variants, key=lambda variant: variant.bitrate)

    async def handle_multiple_media(
        self, message: Message, tweet: TweetData, text: str, api: TwitterAPI
    ) -> None:
        media_list: list[InputMediaPhoto | InputMediaVideo] = []
        for media in tweet.media:
            if media.type == "photo":
                media_list.append(InputMediaPhoto(media.binary_io))

            if media.type in {"video", "gif"}:
                thumbnail_io = await api._url_to_binary_io(media.thumbnail_url)
                variant = variant if (variant := await self.get_best_variant(media)) else media

                media_list.append(
                    InputMediaVideo(
                        media=variant.binary_io,
                        duration=int(
                            timedelta(milliseconds=media.duration).total_seconds() * 1000
                        ),
                        width=media.width,
                        height=media.height,
                        thumb=thumbnail_io,  # type: ignore
                    )
                )

        if not media_list:
            return

        media_list[-1].caption = text
        await message.reply_media_group(media=media_list)

    @router.message(F.text.regexp(URL_PATTERN, search=True))
    async def handle(self, client: Client, message: Message) -> None:
        url = URL_PATTERN.search(message.text)
        if not url:
            return

        api = TwitterAPI()

        try:
            await api.fetch(url.group())
        except TwitterError:
            await message.reply_text(
                _(
                    "Failed to scan your link! This may be due to an incorrect link, "
                    "private/suspended account, deleted tweet, or recent changes to "
                    "Twitter's API."
                )
            )
            return

        tweet = api.tweet

        if not tweet.media:
            await message.reply_text(_("No media found in this tweet!"))
            return

        text = f"<b>{tweet.author.name} (<code>@{tweet.author.screen_name}</code>):</b>\n\n"
        if tweet.text:
            text += f"{tweet.text[:900]}{"..." if len(tweet.text) > 900 else ""}"

        if tweet.source:
            text += _("\n\n<b>Sent from:</b> <i>{source}</i>").format(source=tweet.source)

        async with ChatActionSender(
            client=client, chat_id=message.chat.id, action=ChatAction.UPLOAD_DOCUMENT
        ):
            if len(tweet.media) > 1:
                text += f"\n<a href='{tweet.url}'>Open in Twitter</a>"
                await self.handle_multiple_media(message, tweet, text, api)
                return

            media = tweet.media[0]

            keyboard = InlineKeyboardBuilder()
            keyboard.button(text=_("Open in Twitter"), url=tweet.url)

            if media.type == "photo":
                await client.send_photo(
                    chat_id=message.chat.id,
                    photo=media.binary_io,
                    caption=text,
                    reply_markup=keyboard.as_markup(),
                    reply_to_message_id=message.id,
                )
                return

            if media.type in {"video", "gif"}:
                thumbnail_io = await api._url_to_binary_io(media.thumbnail_url)
                variant = variant if (variant := await self.get_best_variant(media)) else media

                await client.send_video(
                    chat_id=message.chat.id,
                    video=variant.binary_io,
                    caption=text,
                    reply_markup=keyboard.as_markup(),
                    duration=int(timedelta(milliseconds=media.duration).total_seconds() * 1000),
                    width=media.width,
                    height=media.height,
                    thumb=thumbnail_io,
                    reply_to_message_id=message.id,
                )
                return

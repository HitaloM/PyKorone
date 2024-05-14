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
from korone.modules.media_dl.utils.twitter import TweetData, TwitterError, VxTwitterAPI
from korone.utils.i18n import gettext as _

URL_PATTERN = re.compile(r"(?:(?:http|https):\/\/)?(?:www.)?(twitter\.com|x\.com)/.+?/status/\d+")


class TwitterHandler(MessageHandler):
    @staticmethod
    async def handle_multiple_media(message: Message, tweet: TweetData, text: str) -> None:
        media_list: list[InputMediaPhoto | InputMediaVideo] = []
        for media in tweet.media_extended:
            if media.type == "image":
                media_list.append(InputMediaPhoto(media.binary_io))

            if media.type in {"video", "gif"}:
                media_list.append(
                    InputMediaVideo(
                        media=media.binary_io,
                        duration=int(
                            timedelta(milliseconds=media.duration_millis).total_seconds() * 1000
                        ),
                        width=media.size.width,
                        height=media.size.height,
                        thumb=media.thumbnail_url,
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

        api = VxTwitterAPI()
        async with ChatActionSender(
            client=client, chat_id=message.chat.id, action=ChatAction.UPLOAD_DOCUMENT
        ):
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

            text = f"<b>{tweet.user_name} (<code>@{tweet.user_screen_name}</code>):</b>\n\n"
            text += tweet.text

            if len(tweet.media_extended) != 1:
                await self.handle_multiple_media(message, tweet, text)
                return

            text = re.sub(r"https?://t\.co/\S*", "", text)
            media = tweet.media_extended[0]

            keyboard = InlineKeyboardBuilder()
            keyboard.button(text=_("Open in Twitter"), url=tweet.tweet_url)

            if media.type == "image":
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
                await client.send_video(
                    chat_id=message.chat.id,
                    video=media.binary_io,
                    caption=text,
                    reply_markup=keyboard.as_markup(),
                    duration=int(
                        timedelta(milliseconds=media.duration_millis).total_seconds() * 1000
                    ),
                    width=media.size.width,
                    height=media.size.height,
                    thumb=thumbnail_io,
                    reply_to_message_id=message.id,
                )
                return

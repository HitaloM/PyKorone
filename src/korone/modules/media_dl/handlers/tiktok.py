# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import re
from datetime import timedelta

import httpx
from hairydogm.chat_action import ChatActionSender
from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client, filters
from hydrogram.enums import ChatAction
from hydrogram.types import InputMediaPhoto, InputMediaVideo, Message

from korone.decorators import router
from korone.handlers.abstract import MessageHandler
from korone.modules.media_dl.utils.cache import MediaCache
from korone.modules.media_dl.utils.tiktok import (
    TikTokClient,
    TikTokError,
    TikTokSlideshow,
    TikTokVideo,
)
from korone.utils.i18n import gettext as _

URL_PATTERN = re.compile(
    r"^.*https:\/\/(?:m|www|vm)?\.?tiktok\.com\/((?:.*\b(?:(?:usr|v|embed|user|video|photo)\/|\?shareId=|\&item_id=)(\d+))|\w+)"
)


class TikTokHandler(MessageHandler):
    @staticmethod
    async def get_final_url(url: str) -> str:
        async with httpx.AsyncClient(http2=True, follow_redirects=True) as client:
            response = await client.head(url)
            return str(response.url)

    @staticmethod
    def format_text(media: TikTokVideo | TikTokSlideshow) -> str:
        text = f"<b>{media.author}{":" if media.desc else ""}</b>"
        if media.desc:
            text += f"\n\n{media.desc}"
        return text

    async def process_video(
        self, client: Client, message: Message, media: TikTokVideo, media_id: str
    ) -> None:
        cache = MediaCache(media_id)
        cache_data = await cache.get()
        media_file, duration, width, height, thumb = self.get_video_details(media, cache_data)

        try:
            sent_message = await client.send_video(
                chat_id=message.chat.id,
                video=media_file,
                caption=self.format_text(media),
                duration=duration,
                width=width,
                height=height,
                thumb=thumb,
                reply_markup=self.build_keyboard(message.text),
                reply_to_message_id=message.id,
            )
        except Exception as e:
            await message.reply(_("Failed to send media: {error}").format(error=e))
            return

        cache_ttl = int(timedelta(weeks=1).total_seconds())
        await cache.set(sent_message, cache_ttl) if sent_message else None

    async def process_slideshow(
        self, message: Message, media: TikTokSlideshow, media_id: str
    ) -> None:
        cache = MediaCache(media_id)
        cache_data = await cache.get()
        media_list = self.get_slideshow_details(media, cache_data, message.text)

        if len(media_list) == 1:
            try:
                sent_message = await message.reply_photo(
                    media_list[0].media,
                    caption=self.format_text(media),
                    reply_markup=self.build_keyboard(message.text),
                )
            except Exception as e:
                await message.reply(_("Failed to send media: {error}").format(error=e))
                return
        else:
            try:
                sent_message = await message.reply_media_group(media_list)  # type: ignore
            except Exception as e:
                await message.reply(_("Failed to send media: {error}").format(error=e))
                return

        cache_ttl = int(timedelta(weeks=1).total_seconds())
        await cache.set(sent_message, cache_ttl) if sent_message else None

    @staticmethod
    def get_video_details(media: TikTokVideo, cache_data: dict | None):
        media_file = media.video_file
        duration = (
            int(timedelta(milliseconds=media.duration).total_seconds()) if media.duration else 0
        )
        width, height, thumb = media.width, media.height, media.thumbnail_file

        if cache_data:
            video_data = cache_data.get("video", [{}])[0]
            media_file = video_data.get("file", media.video_file)
            duration = video_data.get("duration", duration)
            width = video_data.get("width", width)
            height = video_data.get("height", height)
            thumb = video_data.get("thumbnail", thumb)

        return media_file, duration, width, height, thumb

    def get_slideshow_details(self, media, cache_data, original_url):
        if cache_data:
            media_list = [
                InputMediaPhoto(media["file"]) for media in cache_data.get("photo", [])
            ] + [
                InputMediaVideo(
                    media=media["file"],
                    duration=media["duration"],
                    width=media["width"],
                    height=media["height"],
                    thumb=media["thumbnail"],
                )
                for media in cache_data.get("video", [])
            ]
        else:
            media_list = [InputMediaPhoto(media) for media in media.images]

        if len(media_list) > 1:
            caption = (
                self.format_text(media) + f"\n<a href='{original_url}'>{_("Open in TikTok")}</a>"
            )
            media_list[-1].caption = caption

        return media_list

    @staticmethod
    def build_keyboard(url: str):
        return InlineKeyboardBuilder().button(text=_("Open in TikTok"), url=url).as_markup()

    @router.message(filters.regex(URL_PATTERN))
    async def handle(self, client: Client, message: Message) -> None:
        url_match = URL_PATTERN.search(message.text)
        if not url_match:
            return

        media_id = url_match.group(2) or url_match.group(1)
        try:
            media_id = int(media_id)
        except ValueError:
            redirect_url = await self.get_final_url(url_match.group())
            url_match = URL_PATTERN.search(redirect_url)
            if not url_match:
                return
            media_id = url_match.group(2)

        tiktok = TikTokClient(str(media_id))

        async with ChatActionSender(
            client=client, chat_id=message.chat.id, action=ChatAction.UPLOAD_DOCUMENT
        ):
            try:
                media = await tiktok.get()
            except TikTokError:
                return

            if not media:
                return

            if isinstance(media, TikTokVideo):
                await self.process_video(client, message, media, str(media_id))
            elif isinstance(media, TikTokSlideshow):
                await self.process_slideshow(message, media, str(media_id))

        tiktok.clear()

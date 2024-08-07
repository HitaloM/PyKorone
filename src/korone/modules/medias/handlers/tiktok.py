# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import asyncio
import re
from datetime import timedelta
from io import BytesIO

import httpx
from hairydogm.chat_action import ChatActionSender
from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.enums import ChatAction
from hydrogram.types import InlineKeyboardMarkup, InputMediaPhoto, InputMediaVideo, Message

from korone.decorators import router
from korone.filters import Regex
from korone.handlers.abstract import MessageHandler
from korone.modules.medias.utils.cache import MediaCache
from korone.modules.medias.utils.files import resize_thumbnail, url_to_bytes_io
from korone.modules.medias.utils.tiktok import (
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
    @router.message(Regex(URL_PATTERN))
    async def handle(self, client: Client, message: Message) -> None:
        url_match = URL_PATTERN.search(message.text)
        if not url_match:
            return

        media_id = await self.extract_media_id(url_match)
        if not media_id:
            return

        tiktok_client = TikTokClient(str(media_id))

        try:
            media = await tiktok_client.get()
            if not media:
                return

            await self.process_media(client, message, media, str(media_id))
        except TikTokError:
            return
        finally:
            tiktok_client.clear()

    async def extract_media_id(self, url_match) -> str | int | None:
        media_id = url_match.group(2) or url_match.group(1)
        try:
            return int(media_id)
        except ValueError:
            redirect_url = await self.resolve_redirect_url(url_match.group())
            if url_match := URL_PATTERN.search(redirect_url):
                return url_match.group(2)
        return None

    async def process_media(self, client: Client, message: Message, media, media_id: str) -> None:
        if isinstance(media, TikTokVideo):
            async with ChatActionSender(
                client=client, chat_id=message.chat.id, action=ChatAction.UPLOAD_VIDEO
            ):
                await self.process_video(client, message, media, media_id)
        elif isinstance(media, TikTokSlideshow):
            async with ChatActionSender(
                client=client, chat_id=message.chat.id, action=ChatAction.UPLOAD_PHOTO
            ):
                await self.process_slideshow(message, media, media_id)

    @staticmethod
    async def resolve_redirect_url(url: str) -> str:
        async with httpx.AsyncClient(http2=True, follow_redirects=True) as client:
            response = await client.head(url)
            return str(response.url)

    @staticmethod
    def format_media_text(media: TikTokVideo | TikTokSlideshow) -> str:
        text = f"<b>{media.author}{":" if media.desc else ""}</b>"
        if media.desc:
            text += f"\n\n{media.desc}"
        return text

    async def process_video(
        self, client: Client, message: Message, media: TikTokVideo, media_id: str
    ) -> None:
        cache = MediaCache(media_id)
        cache_data = await cache.get()
        media_file, duration, width, height, thumb = await self.get_video_details(
            media, cache_data
        )
        caption = self.format_media_text(media)
        keyboard = self.create_keyboard(message.text)

        sent_message = await client.send_video(
            chat_id=message.chat.id,
            video=media_file,
            caption=caption,
            no_sound=True,
            duration=duration,
            width=width,
            height=height,
            thumb=thumb,
            reply_markup=keyboard,
            reply_to_message_id=message.id,
        )

        if sent_message:
            cache_ttl = int(timedelta(weeks=1).total_seconds())
            await cache.set(sent_message, cache_ttl)

    async def process_slideshow(
        self, message: Message, media: TikTokSlideshow, media_id: str
    ) -> None:
        cache = MediaCache(media_id)
        cache_data = await cache.get()
        media_list = await self.get_slideshow_details(media, cache_data, message.text)

        if len(media_list) == 1:
            caption = self.format_media_text(media)
            keyboard = self.create_keyboard(message.text)

            sent_message = await message.reply_photo(
                media_list[0].media,
                caption=caption,
                reply_markup=keyboard,
            )
        else:
            sent_message = await message.reply_media_group(media_list)  # type: ignore

        if sent_message:
            cache_ttl = int(timedelta(weeks=1).total_seconds())
            await cache.set(sent_message, cache_ttl)

    @staticmethod
    async def get_video_details(
        media: TikTokVideo, cache_data: dict | None
    ) -> tuple[BytesIO, int, int, int, BytesIO]:
        media_file = await url_to_bytes_io(media.video_url, video=True)
        thumb_file = await url_to_bytes_io(media.thumbnail_url, video=False)
        width, height, duration = media.width, media.height, media.duration

        if cache_data:
            video_data = cache_data.get("video", [{}])[0]
            media_file = video_data.get("file", media_file)
            duration = video_data.get("duration", duration)
            width = video_data.get("width", width)
            height = video_data.get("height", height)
            thumb_file = video_data.get("thumbnail", thumb_file)
            return media_file, duration, width, height, thumb_file

        await asyncio.to_thread(resize_thumbnail, thumb_file)
        return media_file, duration, width, height, thumb_file

    async def get_slideshow_details(
        self, media: TikTokSlideshow, cache_data: dict | None, original_url: str
    ):
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
            media_list = [
                InputMediaPhoto(await url_to_bytes_io(media, video=False))
                for media in media.images
            ]

        if len(media_list) > 1:
            caption = (
                f"{self.format_media_text(media)}\n"
                f"<a href='{original_url}'>{_("Open in TikTok")}</a>"
            )
            media_list[-1].caption = caption

        return media_list

    @staticmethod
    def create_keyboard(url: str) -> InlineKeyboardMarkup:
        return InlineKeyboardBuilder().button(text=_("Open in TikTok"), url=url).as_markup()

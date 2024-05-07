# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import io
import mimetypes
import re
from datetime import timedelta
from pathlib import Path
from urllib.parse import urlparse

import httpx
from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.types import InputMediaPhoto, InputMediaVideo, Message
from magic_filter import F
from PIL import Image

from korone.decorators import router
from korone.handlers.message_handler import MessageHandler
from korone.modules.media_dl.utils.instagram import (
    TIMEOUT,
    GetInstagram,
    InstaData,
    Media,
    NotFoundError,
)
from korone.modules.utils.filters.magic import Magic
from korone.utils.cache import Cached
from korone.utils.i18n import gettext as _

URL_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?instagram\.com/")
REEL_PATTERN = re.compile(r"(?:reel(?:s?)|p)/(?P<post_id>[A-Za-z0-9_-]+)")
STORIES_PATTERN = re.compile(r"(?:stories)/(?:[^/?#&]+/)?(?P<media_id>[0-9]+)")
POST_ID_PATTERN = re.compile(r"^[A-Za-z0-9\-_]+$")

GRAPH_IMAGE = "GraphImage"
GRAPH_VIDEO = "GraphVideo"
STORY_IMAGE = "StoryImage"
STORY_VIDEO = "StoryVideo"


class InstagramHandler(MessageHandler):
    @staticmethod
    def mediaid_to_code(media_id: int) -> str:
        alphabet = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_"
        num = int(media_id)
        if num == 0:
            return alphabet[0]
        arr = []
        base = len(alphabet)
        while num:
            rem = num % base
            num //= base
            arr.append(alphabet[rem])
        arr.reverse()
        return "".join(arr)

    @staticmethod
    @Cached(timedelta(days=1))
    async def url_to_binary_io(url: str) -> io.BytesIO:
        async with httpx.AsyncClient(timeout=TIMEOUT, http2=True) as session:
            mime_type = mimetypes.guess_type(url)[0]
            if mime_type and mime_type.startswith("video"):
                proxy = await session.get(f"https://envoy.lol/{url}")
                response = proxy if proxy.status_code == 200 else await session.get(url)
            else:
                response = await session.get(url)

            content = response.read()

            file = io.BytesIO(content)
            file_path = Path(urlparse(url).path)
            file.name = file_path.name

            if mime_type and mime_type.startswith("video"):
                return file

            if file_path.suffix.lower() in {".webp", ".heic"}:
                file.name = file_path.with_suffix(".jpeg").name
                image = Image.open(file)
                file_jpg = io.BytesIO()
                image.convert("RGB").save(file_jpg, format="JPEG")
                file_jpg.name = file.name
                return file_jpg

            return file

    def get_post_id_from_message(self, message: Message) -> str | None:
        matches = REEL_PATTERN.findall(message.text)
        if len(matches) == 1:
            return matches[0]
        if media_id := STORIES_PATTERN.findall(message.text):
            try:
                return self.mediaid_to_code(int(media_id[0]))
            except ValueError:
                return None
        else:
            return None

    @staticmethod
    def create_caption_and_keyboard(
        insta: InstaData, post_url: str | None
    ) -> tuple[str, InlineKeyboardBuilder | None]:
        text = f"<b>{insta.username}</b>"
        if insta.caption:
            if len(insta.caption) > 255:
                text += f":\n\n{insta.caption[:255]}..."
            else:
                text += f":\n\n{insta.caption}"

        keyboard = None
        if post_url:
            keyboard = InlineKeyboardBuilder()
            keyboard.button(text=_("Open in Instagram"), url=post_url)

        return text, keyboard

    @staticmethod
    async def reply_with_media(
        message: Message,
        media: Media,
        media_bynary: io.BytesIO,
        text: str,
        keyboard: InlineKeyboardBuilder | None,
    ) -> None:
        if media.type_name in {GRAPH_IMAGE, STORY_IMAGE, STORY_VIDEO}:
            if keyboard:
                await message.reply_photo(
                    media_bynary, caption=text, reply_markup=keyboard.as_markup()
                )
            else:
                await message.reply_photo(media_bynary, caption=text)
        elif media.type_name == GRAPH_VIDEO:
            if keyboard:
                await message.reply_video(
                    media_bynary, caption=text, reply_markup=keyboard.as_markup()
                )
            else:
                await message.reply_video(media_bynary, caption=text)

    async def create_media_list(
        self, insta: InstaData
    ) -> list[InputMediaPhoto | InputMediaVideo] | None:
        media_list = []
        for media in insta.medias:
            media_bynary = await self.url_to_binary_io(media.url)
            if media.type_name in {GRAPH_IMAGE, STORY_IMAGE}:
                media_list.append(InputMediaPhoto(media_bynary))
            if media.type_name in {GRAPH_VIDEO, STORY_VIDEO}:
                media_list.append(InputMediaVideo(media_bynary))
        return media_list

    @router.message(Magic(F.text.regexp(URL_PATTERN)))
    async def handle(self, client: Client, message: Message) -> None:
        post_id = self.get_post_id_from_message(message)
        if not post_id:
            await message.reply_text(_("This Instagram URL is not a valid post or story."))
            return

        try:
            insta = await GetInstagram().get_data(post_id)
        except NotFoundError:
            await message.reply_text(_("Oops! Something went wrong while fetching the post."))
            return

        post_url = URL_PATTERN.search(message.text)
        post_url = post_url.group() if post_url else None
        text, keyboard = self.create_caption_and_keyboard(insta, post_url)

        if len(insta.medias) == 1:
            media = insta.medias[0]
            media_bynary = await self.url_to_binary_io(media.url)
            await self.reply_with_media(message, media, media_bynary, text, keyboard)
            return

        media_list = await self.create_media_list(insta)
        if not media_list:
            return

        media_list[-1].caption = text
        if post_url:
            media_list[-1].caption += f"\n\n<a href='{post_url}'>{_("Open in Instagram")}</a>"
        await message.reply_media_group(media_list)

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2023-present Hitalo M. <https://github.com/HitaloM>

import io
import mimetypes
import re
from pathlib import Path
from urllib.parse import urlparse

import aiohttp
from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.types import InputMediaPhoto, InputMediaVideo, Message
from magic_filter import F
from PIL import Image

from korone.decorators import router
from korone.handlers.message_handler import MessageHandler
from korone.modules.media_dl.utils.instagram import HEADERS, GetInstagram
from korone.modules.utils.filters.magic import Magic
from korone.utils.i18n import gettext as _


class InstagramHandler(MessageHandler):
    def __init__(self) -> None:
        self.url_pattern = re.compile(
            r"((?:https?:\/\/)?(?:www\.)?instagram\.com\/(?:p|reels|reel)\/([^/?#&]+)).*"
        )

    async def url_to_binary_io(self, url: str) -> io.BytesIO:
        async with aiohttp.ClientSession(headers=HEADERS) as session:
            response = await session.get(url)
            content = await response.read()

            file = io.BytesIO(content)
            file_path = Path(urlparse(url).path)
            file.name = file_path.name

            mime_type = mimetypes.guess_type(url)[0]
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

    @router.message(
        Magic(
            F.text.regexp(
                r"(?:https?:\/\/)?(?:www\.)?instagram\.com\/(?:p|reels|reel)\/([^/?#&]+).*"
            )
        )
    )
    async def handle(self, client: Client, message: Message) -> None:
        post_url = self.url_pattern.search(message.text)
        if not post_url:
            return

        post_id = post_url.group(2)
        if not post_id:
            return
        if not re.match(r"^[A-Za-z0-9\-_]+$", post_id):
            return

        insta = await GetInstagram().get_data(post_id)

        if len(insta.medias) == 1:
            media = insta.medias[0]

            text = f"<b>{insta.username}:</b>\n\n"
            text += f"{insta.caption[:900]}"

            keyboard = InlineKeyboardBuilder()
            keyboard.button(text=_("Open in Instagram"), url=post_url.group())

            media_bynary = await self.url_to_binary_io(media.url)
            if "GraphImage" in media.type_name:
                await message.reply_photo(
                    media_bynary, caption=text, reply_markup=keyboard.as_markup()
                )
            elif "GraphVideo" in media.type_name:
                await message.reply_video(
                    media_bynary, caption=text, reply_markup=keyboard.as_markup()
                )
            return

        media_list: list[InputMediaPhoto | InputMediaVideo] = []
        for media in insta.medias:
            media_bynary = await self.url_to_binary_io(media.url)
            if "GraphImage" in media.type_name:
                media_list.append(InputMediaPhoto(media_bynary))
            elif "GraphVideo" in media.type_name:
                media_list.append(InputMediaVideo(media_bynary))

        if not media_list:
            return

        text = f"<b>{insta.username}:</b>\n\n"
        text += f"{insta.caption[:900]}"
        text += f"\n\n<a href='{post_url.group()}'>{_("Open in Instagram")}</a>"
        media_list[-1].caption = text

        await message.reply_media_group(media_list)

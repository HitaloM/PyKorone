# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import re

import httpx
from hairydogm.chat_action import ChatActionSender
from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client, filters
from hydrogram.enums import ChatAction
from hydrogram.types import InputMediaPhoto, Message

from korone.decorators import router
from korone.handlers.abstract import MessageHandler
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

    @router.message(filters.regex(URL_PATTERN))
    async def handle(self, client: Client, message: Message) -> None:
        url_match = URL_PATTERN.search(message.text)
        if not url_match:
            return

        media_id = url_match.group(2)
        if not media_id:
            media_id = url_match.group(1)

        try:
            media_id = int(media_id)
        except ValueError:
            redirect_url = await self.get_final_url(url_match.group())
            url_match = URL_PATTERN.search(redirect_url)
            if not url_match:
                return

            media_id = url_match.group(2)

        tiktok = TikTokClient(url_match.group(2))

        async with ChatActionSender(
            client=client, chat_id=message.chat.id, action=ChatAction.UPLOAD_DOCUMENT
        ):
            try:
                media = await tiktok.get()
            except TikTokError:
                await message.reply_text(_("Failed to fetch TikTok video."))
                return

            if not media:
                await message.reply_text(_("Cannot fetch TikTok media. Sorry!"))
                return

            caption = self.format_text(media)
            keyboard = (
                InlineKeyboardBuilder()
                .button(text=_("Open in TikTok"), url=message.text)
                .as_markup()
            )

            if isinstance(media, TikTokVideo):
                await client.send_video(
                    chat_id=message.chat.id,
                    video=media.video_path,
                    caption=caption,
                    duration=media.duration,
                    width=media.width,
                    height=media.height,
                    thumb=media.thumbnail_path,
                    reply_markup=keyboard,
                    reply_to_message_id=message.id,
                )
            elif isinstance(media, TikTokSlideshow):
                media_list = [InputMediaPhoto(media) for media in media.images]
                if len(media_list) == 1:
                    await message.reply_photo(
                        media_list[0].media, caption=caption, reply_markup=keyboard
                    )
                else:
                    caption += f"\n<a href='{message.text}'>{_("Open in TikTok")}</a>"
                    media_list[-1].caption = caption
                    await message.reply_media_group(media_list)  # type: ignore

        tiktok.clear()

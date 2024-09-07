# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import re
from datetime import timedelta

from hairydogm.chat_action import ChatActionSender
from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram.client import Client
from hydrogram.enums import ChatAction
from hydrogram.types import InputMediaPhoto, InputMediaVideo, Message

from korone.decorators import router
from korone.filters import Regex
from korone.modules.medias.utils.cache import MediaCache
from korone.modules.medias.utils.instagram.scraper import POST_PATTERN, instagram
from korone.utils.i18n import gettext as _

URL_PATTERN = re.compile(r"(?:https?://)?(?:www\.)?instagram\.com/.*?(?=\s|$)")


@router.message(Regex(URL_PATTERN))
async def handle_instagram(client: Client, message: Message) -> None:
    if not message.text:
        return

    url = extract_url(message.text)
    if not url:
        return

    media_list = await instagram(url)
    if not media_list:
        return

    if len(media_list) > 10:  # Telegram's limit
        last_caption = media_list[-1].caption
        media_list = media_list[:10]
        media_list[-1].caption = last_caption

    caption = format_caption(media_list, url)  # type: ignore

    async with ChatActionSender(
        client=client, chat_id=message.chat.id, action=ChatAction.UPLOAD_DOCUMENT
    ):
        sent_message = await send_media(message, media_list, caption, url)  # type: ignore

    post_id = extract_post_id(url)
    if post_id and sent_message:
        await cache_media(post_id, sent_message)


def extract_url(text: str) -> str | None:
    match = URL_PATTERN.search(text)
    return match.group() if match else None


def format_caption(media_list: list, url: str) -> str:
    caption = media_list[-1].caption
    if len(media_list) > 1:
        caption += f"\n<a href='{url}'>📷 {_("Open in Instagram")}</a>"
    return caption


async def send_media(message: Message, media_list: list, caption: str, url: str) -> Message | None:
    if len(media_list) == 1:
        media = media_list[0]
        keyboard = (
            InlineKeyboardBuilder()
            .button(text=f"📷 {_("Open in Instagram")}", url=url)
            .as_markup()
        )
        if isinstance(media, InputMediaPhoto):
            return await message.reply_photo(media.media, caption=caption, reply_markup=keyboard)
        if isinstance(media, InputMediaVideo):
            return await message.reply_video(media.media, caption=caption, reply_markup=keyboard)
        return None
    media_list[-1].caption = caption
    return await message.reply_media_group(media_list)  # type: ignore


def extract_post_id(url: str) -> str | None:
    match = POST_PATTERN.search(url)
    return match.group(1) if match else None


async def cache_media(post_id: str, sent_message: Message) -> None:
    cache = MediaCache(post_id)
    await cache.set(sent_message, expire=int(timedelta(weeks=1).total_seconds()))

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import asyncio
import html
import re
from datetime import timedelta
from typing import cast

import httpx
from hairydogm.chat_action import ChatActionSender
from hydrogram import Client
from hydrogram.enums import ChatAction
from hydrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    InputMediaPhoto,
    InputMediaVideo,
    Message,
)

from korone.decorators import router
from korone.filters import Regex
from korone.modules.medias.utils.cache import MediaCache
from korone.modules.medias.utils.downloader import download_media
from korone.modules.medias.utils.files import resize_thumbnail
from korone.modules.medias.utils.generic_headers import GENERIC_HEADER
from korone.modules.medias.utils.tiktok.scraper import TikTokClient, TikTokError
from korone.modules.medias.utils.tiktok.types import TikTokSlideshow, TikTokVideo
from korone.utils.i18n import gettext as _
from korone.utils.logging import logger

URL_PATTERN = re.compile(
    r"https:\/\/(?:m|www|vm|vt)?\.?tiktok\.com\/((?:.*\b(?:(?:usr|v|embed|user|video|photo)\/|\?shareId=|\&item_id=)(\d+))|\w+)"
)


@router.message(Regex(URL_PATTERN))
async def handle_tiktok(client: Client, message: Message) -> None:
    if not message.text:
        return

    url_match = URL_PATTERN.search(message.text)
    if not url_match:
        return

    tiktok_url = url_match.group(0)
    media_id = await extract_media_id(url_match)
    if not media_id:
        return

    tiktok_client = TikTokClient(str(media_id))

    try:
        media = await tiktok_client.get()
        if not media:
            return

        await process_media(client, message, media, str(media_id), tiktok_url)
    except TikTokError:
        return
    finally:
        tiktok_client.clear()


async def extract_media_id(url_match: re.Match[str]) -> str | int | None:
    media_id_str = url_match.group(2) or url_match.group(1)
    try:
        return int(media_id_str)
    except ValueError:
        redirect_url = await resolve_redirect_url(url_match.group(0))
        if redirect_url and (match := URL_PATTERN.search(redirect_url)):
            return match.group(2)
    return None


async def resolve_redirect_url(url: str) -> str | None:
    try:
        async with httpx.AsyncClient(
            http2=True, timeout=20, follow_redirects=True, headers=GENERIC_HEADER
        ) as client:
            response = await client.head(url)
            if response.url:
                return str(response.url)
            response.raise_for_status()
    except (httpx.RequestError, httpx.HTTPStatusError) as e:
        await logger.aerror(
            "[Medias/TikTok] An error occurred while requesting %s.", str(e.request.url)
        )
        return None


async def process_media(
    client: Client,
    message: Message,
    media: TikTokVideo | TikTokSlideshow,
    media_id: str,
    tiktok_url: str,
) -> None:
    if isinstance(media, TikTokVideo):
        await process_video(client, message, media, media_id, tiktok_url)
    elif isinstance(media, TikTokSlideshow):
        await process_slideshow(message, media, media_id, tiktok_url)


async def process_video(
    client: Client, message: Message, media: TikTokVideo, media_id: str, tiktok_url: str
) -> None:
    async with ChatActionSender(
        client=client, chat_id=message.chat.id, action=ChatAction.UPLOAD_VIDEO
    ):
        cache = MediaCache(media_id)
        cache_data = await cache.get()
        media_file = (
            cast("InputMediaVideo", cache_data[0])
            if cache_data
            else await prepare_video_media(media)
        )

        caption = format_media_text(media)
        keyboard = create_keyboard(tiktok_url)

        sent_message = await message.reply_video(
            video=media_file.media,
            caption=caption,
            no_sound=True,
            duration=media_file.duration,
            width=media_file.width,
            height=media_file.height,
            thumb=media_file.thumb,
            reply_markup=keyboard,
            reply_to_message_id=message.id,
        )

        if sent_message:
            await cache.set(sent_message, int(timedelta(weeks=1).total_seconds()))


async def process_slideshow(
    message: Message, media: TikTokSlideshow, media_id: str, tiktok_url: str
) -> None:
    async with ChatActionSender(
        client=message._client, chat_id=message.chat.id, action=ChatAction.UPLOAD_PHOTO
    ):
        cache = MediaCache(media_id)
        media_list = await cache.get() or await prepare_slideshow_media(media)

        media_list[
            -1
        ].caption = f"{format_media_text(media)}\n<a href='{tiktok_url}'>{_('Open in TikTok')}</a>"

        if len(media_list) == 1:
            caption = format_media_text(media)
            keyboard = create_keyboard(tiktok_url)

            sent_message = await message.reply_photo(
                media_list[0].media,
                caption=caption,
                reply_markup=keyboard,
            )
        else:
            if len(media_list) > 10:  # Telegram's limit
                media_list = media_list[:10]

            sent_message = await message.reply_media_group(media_list)  # type: ignore

        if sent_message:
            await cache.set(sent_message, int(timedelta(weeks=1).total_seconds()))


async def prepare_video_media(media: TikTokVideo) -> InputMediaVideo:
    media_file = await download_media(str(media.video_url))
    if not media_file:
        msg = "Failed to download video."
        raise TikTokError(msg)

    thumb_file = await download_media(str(media.thumbnail_url))
    if not thumb_file:
        msg = "Failed to download thumbnail."
        raise TikTokError(msg)

    await asyncio.to_thread(resize_thumbnail, thumb_file)
    return InputMediaVideo(
        media=media_file,
        duration=media.duration,
        width=media.width,
        height=media.height,
        thumb=thumb_file,
    )


async def prepare_slideshow_media(media: TikTokSlideshow) -> list[InputMediaPhoto]:
    media_list = []
    for image in media.images:
        media_file = await download_media(str(image))
        if media_file:
            media_list.append(InputMediaPhoto(media=media_file))
        else:
            msg = "Failed to download image."
            raise TikTokError(msg)
    return media_list


def format_media_text(media: TikTokVideo | TikTokSlideshow) -> str:
    text = f"<b>{media.author}{':' if media.desc else ''}</b>"
    if media.desc:
        text += html.escape(f"\n{media.desc[:900]}{'...' if len(media.desc) > 900 else ''}")
    return text


def create_keyboard(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[InlineKeyboardButton(_("Open in TikTok"), url=url)]])

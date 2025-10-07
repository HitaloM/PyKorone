# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import html
import re

from anyio import Path
from babel.numbers import format_number
from hairydogm.chat_action import ChatActionSender
from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.enums import ChatAction
from hydrogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from korone.decorators import router
from korone.filters import Command, CommandObject
from korone.modules.medias.callback_data import YtGetCallback, YtMediaType
from korone.modules.medias.utils.youtube.types import VideoInfo
from korone.modules.medias.utils.youtube.ytdl import (
    DownloadError,
    InfoExtractionError,
    YtdlpManager,
)
from korone.utils.i18n import get_i18n
from korone.utils.i18n import gettext as _

YOUTUBE_REGEX = re.compile(
    r"""
    https?://
    (?:www\.)?
    (?:music\.)?
    youtu(?:be\.com/
        (?:
            watch\?v= |
            shorts/   |
            embed/
        )
    |\.be/)
    ([^\s&]+)
    """,
    re.VERBOSE | re.IGNORECASE,
)


@router.message(Command("ytdl"))
async def ytdl_command(client: Client, message: Message) -> None:
    args = await get_args(CommandObject(message).parse(), message)
    if args is None:
        return

    ytdl = YtdlpManager()
    async with ChatActionSender(client=client, chat_id=message.chat.id):
        yt_info = await fetch_video_info(ytdl, args, message)
        if not yt_info:
            return
        text = build_video_info_text(yt_info)
        keyboard = build_keyboard(yt_info)
        await message.reply(text, reply_markup=keyboard)


async def get_args(command: CommandObject, message: Message) -> str | None:
    if command.args:
        return command.args
    if (reply := message.reply_to_message) and reply.text:
        return reply.text
    await message.reply(_("Provide a search query or URL, or reply with one."))
    return None


async def fetch_video_info(ytdl: YtdlpManager, query: str, message: Message) -> VideoInfo | None:
    try:
        url = query if YOUTUBE_REGEX.search(query) else f"ytsearch:{query}"
        return await ytdl.get_video_info(url)
    except InfoExtractionError:
        await message.reply(_("Failed to extract video info!"))
        return None


def format_duration(duration: int) -> str:
    hours, remainder = divmod(duration, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{_('<b>Duration:</b>')} {hours}h {minutes}m {seconds}s\n"
    if minutes:
        return f"{_('<b>Duration:</b>')} {minutes}m {seconds}s\n"
    return f"{_('<b>Duration:</b>')} {seconds}s\n"


def build_video_info_text(yt_info: VideoInfo) -> str:
    locale = get_i18n().current_locale
    likes_text = (
        f"{_('<b>Likes:</b>')} {format_number(yt_info.like_count, locale=locale)}\n"
        if yt_info.like_count is not None
        else f"{_('<b>Likes:</b>')} {_('Unknown')}\n"
    )
    return (
        f"{_('<b>Title:</b>')} {html.escape(yt_info.title)}\n"
        f"{_('<b>Uploader:</b>')} {html.escape(yt_info.uploader)}\n"
        f"{format_duration(yt_info.duration)}"
        f"{_('<b>Views:</b>')} {format_number(yt_info.view_count, locale=locale)}\n"
        f"{likes_text}"
    )


def build_keyboard(yt_info: VideoInfo) -> InlineKeyboardMarkup:
    keyboard = InlineKeyboardBuilder()
    keyboard.button(
        text=_("Download video"),
        callback_data=YtGetCallback(media_id=yt_info.video_id, media_type=YtMediaType.Video),
    )
    keyboard.button(
        text=_("Download audio"),
        callback_data=YtGetCallback(media_id=yt_info.video_id, media_type=YtMediaType.Audio),
    )
    return keyboard.as_markup()


@router.callback_query(YtGetCallback.filter())
async def handle_ytdl_callback(client: Client, callback: CallbackQuery) -> None:
    if not callback.data:
        return
    query = YtGetCallback.unpack(callback.data)
    match query.media_type:
        case YtMediaType.Video | YtMediaType.Audio:
            url = f"https://www.youtube.com/watch?v={query.media_id}"
            await download_and_send_media(client, callback, url, query.media_type)


async def download_and_send_media(
    client: Client, callback: CallbackQuery, url: str, media_type: YtMediaType
) -> None:
    ytdl = YtdlpManager()
    message = callback.message
    match media_type:
        case YtMediaType.Video:
            action = ChatAction.UPLOAD_VIDEO
            download_method = ytdl.download_video
        case YtMediaType.Audio:
            action = ChatAction.UPLOAD_AUDIO
            download_method = ytdl.download_audio
        case _:
            return

    await message.edit(_("Downloading..."))
    yt = await download_and_handle(download_method, url, message)
    if not yt:
        return

    await message.edit(_("Uploading..."))
    caption = f"<a href='{url}'>{yt.title}</a>"
    await upload_media(client, message, action, media_type, ytdl, yt, caption)
    await message.delete()
    await ytdl.clear()


async def download_and_handle(download_method, url: str, message: Message) -> VideoInfo | None:
    try:
        return await download_method(url)
    except DownloadError as e:
        text = (
            "Sorry, I am unable to download this media. It may exceed the 300MB size limit."
            if "requested format is not available" in str(e).lower()
            else _("Failed to download the media.")
        )
        await message.edit(text)
        return None


async def upload_media(
    client: Client,
    message: Message,
    action: ChatAction,
    media_type: YtMediaType,
    ytdl: YtdlpManager,
    yt: VideoInfo,
    caption: str,
) -> None:
    if not ytdl.file_path:
        await message.edit(_("Failed to download the media."))
        return
    async with ChatActionSender(client=client, chat_id=message.chat.id, action=action):
        thumb = Path(str(yt.thumbnail)).as_posix() if yt.thumbnail else None
        match media_type:
            case YtMediaType.Video:
                await client.send_video(
                    message.chat.id,
                    video=ytdl.file_path,
                    caption=caption,
                    no_sound=True,
                    duration=yt.duration,
                    thumb=thumb,
                    height=yt.height,
                    width=yt.width,
                )
            case YtMediaType.Audio:
                await client.send_audio(
                    message.chat.id,
                    audio=ytdl.file_path,
                    caption=caption,
                    duration=yt.duration,
                    performer=yt.uploader,
                    title=yt.title,
                    thumb=thumb,
                )

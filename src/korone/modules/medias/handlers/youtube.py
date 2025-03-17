# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2025 Hitalo M. <https://github.com/HitaloM>

import html
import re

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
    command = CommandObject(message).parse()
    args = await get_args(command, message)
    if not args:
        return

    if not YOUTUBE_REGEX.search(args):
        await message.reply(_("Invalid YouTube URL!"))
        return

    ytdl = YtdlpManager()
    chat_id = message.chat.id

    async with ChatActionSender(client=client, chat_id=chat_id):
        yt_info = await fetch_video_info(ytdl, args, message)
        if not yt_info:
            return

        text = build_video_info_text(yt_info)
        keyboard = build_keyboard(yt_info)
        await message.reply(text, reply_markup=keyboard)


async def get_args(command: CommandObject, message: Message) -> str | None:
    if command.args:
        return command.args
    if message.reply_to_message and message.reply_to_message.text:
        if args_match := YOUTUBE_REGEX.search(message.reply_to_message.text):
            return args_match.group()
        await message.reply(_("No YouTube URL found in the replied message."))
        return None
    await message.reply(
        _(
            "You need to provide a URL or reply to a message that contains a URL. "
            "Example: <code>/ytdl https://www.youtube.com/watch?v=dQw4w9WgXcQ</code>"
        )
    )
    return None


async def fetch_video_info(ytdl: YtdlpManager, url: str, message: Message) -> VideoInfo | None:
    try:
        return await ytdl.get_video_info(url)
    except InfoExtractionError:
        await message.reply(_("Failed to extract video info!"))
        return None


def build_video_info_text(yt_info: VideoInfo) -> str:
    text = _("<b>Title:</b> {title}\n").format(title=html.escape(yt_info.title))
    text += _("<b>Uploader:</b> {uploader}\n").format(uploader=html.escape(yt_info.uploader))

    match yt_info.duration:
        case duration if duration >= 3600:
            hours, remaining_seconds = divmod(duration, 3600)
            minutes, seconds = divmod(remaining_seconds, 60)
            text += _("<b>Duration:</b> {hours}h {minutes}m {seconds}s\n").format(
                hours=hours, minutes=minutes, seconds=seconds
            )
        case duration if duration >= 60:
            minutes, seconds = divmod(duration, 60)
            text += _("<b>Duration:</b> {minutes}m {seconds}s\n").format(
                minutes=minutes, seconds=seconds
            )
        case seconds:
            text += _("<b>Duration:</b> {seconds}s\n").format(seconds=seconds)

    locale = get_i18n().current_locale
    view_count = format_number(yt_info.view_count, locale=locale)
    text += _("<b>Views:</b> {view_count}\n").format(view_count=view_count)

    if yt_info.like_count is None:
        text += _("<b>Likes:</b> Unknown\n")
    else:
        like_count = format_number(yt_info.like_count, locale=locale)
        text += _("<b>Likes:</b> {like_count}\n").format(like_count=like_count)

    return text


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
    if query.media_type in {YtMediaType.Video, YtMediaType.Audio}:
        url = f"https://www.youtube.com/watch?v={query.media_id}"
        await download_and_send_media(client, callback, url, query.media_type)


async def download_and_send_media(
    client: Client, callback: CallbackQuery, url: str, media_type: YtMediaType
) -> None:
    ytdl = YtdlpManager()
    message = callback.message
    action = (
        ChatAction.UPLOAD_VIDEO if media_type == YtMediaType.Video else ChatAction.UPLOAD_AUDIO
    )
    download_method = (
        ytdl.download_video if media_type == YtMediaType.Video else ytdl.download_audio
    )

    await message.edit(_("Downloading..."))
    yt = await download_media(download_method, url, message)
    if not yt:
        return

    await message.edit(_("Uploading..."))
    caption = f"<a href='{url}'>{yt.title}</a>"

    await upload_media(client, message, action, media_type, ytdl, yt, caption)
    await message.delete()
    ytdl.clear()


async def download_media(download_method, url: str, message: Message) -> VideoInfo | None:
    try:
        return await download_method(url)
    except DownloadError as e:
        if "requested format is not available" in str(e).lower():
            text = "Sorry, I am unable to download this media. It may exceed the 300MB size limit."
        else:
            text = _("Failed to download the media.")
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
        if media_type == YtMediaType.Video:
            await client.send_video(
                message.chat.id,
                video=ytdl.file_path,
                caption=caption,
                no_sound=True,
                duration=yt.duration,
                thumb=yt.thumbnail.as_posix() if yt.thumbnail else None,
                height=yt.height,
                width=yt.width,
            )
        else:
            await client.send_audio(
                message.chat.id,
                audio=ytdl.file_path,
                caption=caption,
                duration=yt.duration,
                performer=yt.uploader,
                title=yt.title,
                thumb=yt.thumbnail.as_posix() if yt.thumbnail else None,
            )

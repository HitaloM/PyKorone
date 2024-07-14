# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import re

from babel.numbers import format_number
from hairydogm.chat_action import ChatActionSender
from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.enums import ChatAction
from hydrogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from korone.decorators import router
from korone.filters import Command, CommandObject
from korone.handlers.abstract import CallbackQueryHandler, MessageHandler
from korone.modules.medias.callback_data import YtGetCallback
from korone.modules.medias.utils.youtube import (
    DownloadError,
    InfoExtractionError,
    VideoInfo,
    YtdlpManager,
)
from korone.utils.i18n import get_i18n
from korone.utils.i18n import gettext as _

YOUTUBE_REGEX = re.compile(
    r"(?m)http(?:s?):\/\/(?:www\.)?(?:music\.)?youtu(?:be\.com\/(watch\?v=|shorts/|embed/)|\.be\/)[^\s&]+"
)


class YouTubeHandler(MessageHandler):
    @staticmethod
    def build_text(yt_info: VideoInfo) -> str:
        text = _("<b>Title:</b> {title}\n").format(title=yt_info.title)
        text += _("<b>Uploader:</b> {uploader}\n").format(uploader=yt_info.uploader)

        hours, minutes, seconds = 0, 0, 0
        if yt_info.duration >= 3600:
            hours, remaining_seconds = divmod(yt_info.duration, 3600)
            minutes, seconds = divmod(remaining_seconds, 60)
        elif yt_info.duration >= 60:
            minutes, seconds = divmod(yt_info.duration, 60)
        else:
            seconds = yt_info.duration

        if hours > 0:
            text += _("<b>Duration:</b> {hours}h {minutes}m {seconds}s\n").format(
                hours=hours, minutes=minutes, seconds=seconds
            )
        elif minutes > 0:
            text += _("<b>Duration:</b> {minutes}m {seconds}s\n").format(
                minutes=minutes, seconds=seconds
            )
        else:
            text += _("<b>Duration:</b> {seconds}s\n").format(seconds=seconds)

        locale = get_i18n().current_locale

        view_count = format_number(yt_info.view_count, locale=locale)
        like_count = format_number(yt_info.like_count, locale=locale)

        text += _("<b>Views:</b> {view_count}\n").format(view_count=view_count)
        text += _("<b>Likes:</b> {like_count}\n").format(like_count=like_count)

        return text

    @staticmethod
    def build_keyboard(yt_info: VideoInfo) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(
            text=_("Download video"),
            callback_data=YtGetCallback(media_id=yt_info.video_id, media_type="video"),
        )
        keyboard.button(
            text=_("Download audio"),
            callback_data=YtGetCallback(media_id=yt_info.video_id, media_type="audio"),
        )
        return keyboard.as_markup()

    @router.message(Command("ytdl"))
    async def handle(self, client: Client, message: Message) -> None:
        command = CommandObject(message).parse()

        if command.args:
            args = command.args

        elif message.reply_to_message and message.reply_to_message.text:
            args = YOUTUBE_REGEX.search(message.reply_to_message.text)
            if not args:
                await message.reply(_("No YouTube URL found in the replied message."))
                return

            args = args.group()

        else:
            await message.reply(
                _(
                    "You need to provide a URL or reply to a message that contains a URL. "
                    "Example: <code>/ytdl https://www.youtube.com/watch?v=dQw4w9WgXcQ</code>"
                )
            )
            return

        if not YOUTUBE_REGEX.search(args):
            await message.reply(_("Invalid YouTube URL!"))
            return

        ytdl = YtdlpManager()

        chat_id = message.chat.id
        async with ChatActionSender(client=client, chat_id=chat_id):
            try:
                yt_info = await ytdl.get_video_info(args)
            except InfoExtractionError:
                await message.reply(_("Failed to extract video info!"))
                return

            text = self.build_text(yt_info)
            keyboard = self.build_keyboard(yt_info)

            await message.reply(text, reply_markup=keyboard)


class GetYouTubeHandler(CallbackQueryHandler):
    @staticmethod
    async def download_media(client: Client, callback: CallbackQuery, url: str, media_type: str):
        ytdl = YtdlpManager()

        message = callback.message

        action = ChatAction.UPLOAD_VIDEO if media_type == "video" else ChatAction.UPLOAD_AUDIO
        download_method = ytdl.download_video if media_type == "video" else ytdl.download_audio

        await message.edit(_("Downloading..."))

        try:
            yt = await download_method(url)
        except DownloadError as err:
            if "requested format is not available" in str(err).lower():
                text = (
                    "Sorry, I am unable to download this media. "
                    "It may exceed the 300MB size limit."
                )
            else:
                text = _("Failed to download the media.")

            await message.edit(text)
            return

        if not ytdl.file_path:
            await message.edit(_("Failed to download the media."))
            return

        await message.edit(_("Uploading..."))

        caption = f"<a href='{yt.url}'>{yt.title}</a>"

        try:
            async with ChatActionSender(client=client, chat_id=message.chat.id, action=action):
                if media_type == "video":
                    await client.send_video(
                        message.chat.id,
                        video=ytdl.file_path,
                        caption=caption,
                        no_sound=True,
                        duration=yt.duration,
                        thumb=yt.thumbnail,
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
                        thumb=yt.thumbnail,
                    )
            await message.delete()
        except Exception:
            await message.edit(_("Failed to send the media."))
        finally:
            ytdl.clear()

    @router.callback_query(YtGetCallback.filter())
    async def handle(self, client: Client, callback: CallbackQuery) -> None:
        if not callback.data:
            return

        query = YtGetCallback.unpack(callback.data)
        if query.media_type in {"video", "audio"}:
            url = f"https://www.youtube.com/watch?v={query.media_id}"

            await self.download_media(client, callback, url, query.media_type)

# SPDX-License-Identifier: BSD-3-Clause
# Copyright (c) 2024 Hitalo M. <https://github.com/HitaloM>

import re

from hairydogm.chat_action import ChatActionSender
from hairydogm.keyboard import InlineKeyboardBuilder
from hydrogram import Client
from hydrogram.enums import ChatAction
from hydrogram.types import CallbackQuery, InlineKeyboardMarkup, Message

from korone.decorators import router
from korone.handlers.abstract.callback_query_handler import CallbackQueryHandler
from korone.handlers.abstract.message_handler import MessageHandler
from korone.modules.media_dl.callback_data import YtGetCallback
from korone.modules.media_dl.utils.youtube import (
    DownloadError,
    FileSizeError,
    InfoExtractionError,
    VideoInfo,
    YtdlpManager,
)
from korone.modules.utils.filters import Command, CommandObject
from korone.utils.i18n import gettext as _

YOUTUBE_REGEX = re.compile(
    r"(?m)http(?:s?):\/\/(?:www\.)?(?:music\.)?youtu(?:be\.com\/(watch\?v=|shorts/|embed/)|\.be\/)[^\s&]+"
)


class YouTubeHandler(MessageHandler):
    @staticmethod
    def build_text(yt_info: VideoInfo) -> str:
        text = _("<b>Title:</b> {title}\n").format(title=yt_info.title)
        text += _("<b>Uploader:</b> {uploader}\n").format(uploader=yt_info.uploader)

        if yt_info.duration >= 60:
            minutes = yt_info.duration // 60
            seconds = yt_info.duration % 60
            text += _("<b>Duration:</b> {minutes}m {seconds}s\n").format(
                minutes=minutes, seconds=seconds
            )
        else:
            text += _("<b>Duration:</b> {seconds}s\n").format(seconds=yt_info.duration)

        view_count = f"{yt_info.view_count:,}"
        like_count = f"{yt_info.like_count:,}"

        text += _("<b>Views:</b> {views}\n").format(views=view_count)
        text += _("<b>Likes:</b> {likes}\n").format(likes=like_count)

        return text

    @staticmethod
    def build_keyboard(yt_info: VideoInfo) -> InlineKeyboardMarkup:
        keyboard = InlineKeyboardBuilder()
        keyboard.button(
            text=_("Download video"),
            callback_data=YtGetCallback(media_id=yt_info.id, media_type="video"),
        )
        keyboard.button(
            text=_("Download audio"),
            callback_data=YtGetCallback(media_id=yt_info.id, media_type="audio"),
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
                _("You need to provide a URL or reply to a message that contains a URL.")
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
    async def download_media(client, callback, url, media_type):
        ytdl = YtdlpManager()

        chat_id = callback.message.chat.id
        action = ChatAction.UPLOAD_VIDEO if media_type == "video" else ChatAction.UPLOAD_AUDIO
        download_method = ytdl.download_video if media_type == "video" else ytdl.download_audio

        async with ChatActionSender(client=client, chat_id=chat_id, action=action):
            try:
                yt, file_path = await download_method(url)
            except DownloadError:
                await callback.answer(_("Failed to download {media_type}!"))
                return
            except FileSizeError:
                await callback.answer(
                    _("{media_type.capitalize()} exceeds Telegram's file size limit!")
                )
                return

            caption = f"<a href='{yt.url}'>{yt.title}</a>"
            if media_type == "video":
                await client.send_video(
                    chat_id,
                    video=file_path,
                    caption=caption,
                    duration=yt.duration,
                    thumb=yt.thumbnail,
                    height=yt.height,
                    width=yt.width,
                )
            else:
                await client.send_audio(
                    chat_id,
                    audio=file_path,
                    caption=caption,
                    duration=yt.duration,
                    performer=yt.uploader,
                    title=yt.title,
                    thumb=yt.thumbnail,
                )
            ytdl.clear()

    @router.callback_query(YtGetCallback.filter())
    async def handle(self, client: Client, callback: CallbackQuery) -> None:
        if not callback.data:
            return

        query = YtGetCallback.unpack(callback.data)
        url = f"https://www.youtube.com/watch?v={query.media_id}"

        if query.media_type in {"video", "audio"}:
            await self.download_media(client, callback, url, query.media_type)
